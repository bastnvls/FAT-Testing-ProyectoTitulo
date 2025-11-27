from datetime import datetime, timedelta
from flask import Flask, request, render_template, send_file, redirect, url_for, flash, jsonify, json
from werkzeug.utils import secure_filename
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from copy import deepcopy
from PIL import Image
from io import BytesIO
import os
import re
from docx.shared import Inches
from funcionalidades.resaltado import subrayar_texto
from flask_login import LoginManager, login_required, current_user, login_user
from flask_mail import Mail
from models import db, bcrypt, User, PasswordResetToken
from config import Config
from utils import validate_password_strength, validate_email_format, send_password_reset_email
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar extensiones
db.init_app(app)
bcrypt.init_app(app)
mail = Mail(app)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

@login_manager.user_loader
def load_user(user_id):
    """
    Propósito: cargar el usuario desde la sesión para Flask-Login.
    Entradas: user_id (str/int) guardado en la cookie de sesión.
    Salidas: instancia de User o None.
    Dependencias: User.query.get (usa el modelo nuevo con PK entera).
    """
    try:
        return User.query.get(int(user_id))  # Busca por PK entera
    except (TypeError, ValueError):
        return None  # Si no es un ID válido, no devuelve usuario

def aplicar_fuente_cascadia_code(run, size_pt):
    run.font.name = 'Cascadia Code'
    run.font.size = Pt(size_pt)
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Cascadia Code')

def limpiar_texto_xml(texto):
    """
    Limpia el texto de caracteres incompatibles con XML.
    Elimina NULL bytes y caracteres de control excepto tab, newline y carriage return.

    Args:
        texto: String a limpiar

    Returns:
        String limpio compatible con XML
    """
    if not texto:
        return texto

    # Eliminar NULL bytes
    texto = texto.replace('\x00', '')

    # Eliminar caracteres de control (0x00-0x1F) excepto tab (0x09), newline (0x0A), carriage return (0x0D)
    # También eliminar DEL (0x7F) y caracteres de control en rango extendido (0x80-0x9F)
    caracteres_permitidos = []
    for char in texto:
        code = ord(char)
        # Permitir caracteres normales, tab, newline, carriage return
        if code >= 0x20 or code in (0x09, 0x0A, 0x0D):
            # Excluir DEL y caracteres de control extendidos
            if code != 0x7F and not (0x80 <= code <= 0x9F):
                caracteres_permitidos.append(char)

    return ''.join(caracteres_permitidos)

# Función para extraer bloques
def pruebas(lines, start_re, end_re):
    blocks = []
    collecting = False
    current = []
    for line in lines:
        stripped = line.strip()
        if not collecting and start_re.match(stripped):
            collecting = True
            current = [line]
            continue

        if collecting:
            current.append(line)
            if end_re.match(stripped):
                blocks.append('\n'.join(current))
                collecting = False
    return blocks

def iter_paragraphs(doc):
        for p in doc.paragraphs:
            yield p
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        yield p


# EMu_PER_INCH define cuántas EMUs (English Metric Units) hay en una pulgada.
# Un EMU es la unidad mínima de medida interna que Word usa para posicionar y dimensionar objetos.
# A 914400 EMUs por pulgada, se logra precisión subpíxel en el tamaño de imágenes y elementos gráficos.
EMu_PER_INCH = 914400

def _get_image_emu_size(image_bytes):
    """
    Propósito:
        Convertir el tamaño de una imagen de píxeles a EMUs (English Metric Units)
        para que Word pueda insertarla con dimensiones exactas.

    Entradas:
        image_bytes (bytes): Bytes crudos de la imagen (cabeceras + datos).

    Salidas:
        (int, int): Tupla (cx, cy) con ancho y alto en EMUs.

    Dependencias:
        - PIL.Image: abre el contenido en memoria y obtiene tamaño y DPI.
        - io.BytesIO: envuelve los bytes para simular un archivo.
        - EMu_PER_INCH: factor de conversión de pulgadas a EMUs.
    """
    # 1) Crear un buffer en memoria para que PIL lo reconozca como archivo
    img = Image.open(BytesIO(image_bytes))

    # 2) Obtener anchura y altura en píxeles
    px_w, px_h = img.size

    # 3) Obtener DPI horizontal y vertical desde metadatos; si faltan, usar 96 DPI
    dpi_x, dpi_y = img.info.get('dpi', (96, 96))
    dpi_x = dpi_x or 96  # evitar división por cero
    dpi_y = dpi_y or 96

    # 4) Calcular ancho (cx) y alto (cy) en EMUs:
    #    EMUs = (píxeles / DPI) * EMUs_por_pulgada
    cx = int(px_w / dpi_x * EMu_PER_INCH)
    cy = int(px_h / dpi_y * EMu_PER_INCH)

    # 5) Devolver dimensiones convertidas
    return cx, cy

def reemplazar_imagen_flotante(doc, marker, image_file):
    """
    Propósito:
        Localizar en el XML interno del documento (.docx) el primer
        <w:drawing> cuyo <pic:cNvPr descr> coincide con `marker`, y reemplazar
        esa imagen por la subida, ajustando la referencia interna (rId) y tamaño.

    Entradas:
        doc (docx.Document): Documento abierto con python-docx.
        marker (str): Valor de atributo descr en <pic:cNvPr> que marca el placeholder.
        image_file (FileStorage): Imagen subida desde Flask, con método read().

    Salidas:
        None: Modifica `doc` en memoria.

    Dependencias:
        - doc.part.get_or_add_image: agrega la imagen al ZIP interno y devuelve rId.
        - _get_image_emu_size: calcula cx, cy para <wp:extent>.
        - doc.element.xpath: navegación por el XML WML con lxml.
        - qn: función de python-docx para nombres de espacio XML.
    """
    # 1) Leer bytes crudos de la imagen
    image_bytes = image_file.read()

    # 2) Agregar la imagen al paquete y obtener un nuevo rId (Relationship ID)
    #    - En esta línea **se asigna** `new_rId`:
    #         new_rId, _ = doc.part.get_or_add_image(BytesIO(image_bytes))
    #      * `get_or_add_image` calcula un hash de los bytes,
    #        copia el archivo a `word/media/` (si no existía) y crea/modifica
    #        la entrada correspondiente en `document.xml.rels`:
    #          <Relationship Id="rIdX" Type=".../image" Target="media/imageX.ext"/>
    #      * Devuelve:
    #          - `new_rId`: cadena única para referenciar este recurso en el XML (p.ej. "rId7").
    #          - `ImagePart`: objeto interno que representa el recurso agregado.
    new_rId, _ = doc.part.get_or_add_image(BytesIO(image_bytes))

    # 3) Calcular dimensiones en EMU para la imagen
    #    - Usa los bytes leídos para determinar tamaño en unidades EMU (ancho, alto)
    #    - Estas dimensiones se asignarán luego a <wp:extent>
    cx, cy = _get_image_emu_size(image_bytes)

    # 4) Recorrer cada nodo <w:drawing> en el documento
    #    Python‑docx no expone directamente elementos de dibujo, así que trabajamos con el XML:
    #    - <w:drawing> es el contenedor genérico para gráficos (imágenes, formas, etc.).
    #    - Debemos buscar dentro de estos nodos cuál corresponde al placeholder que queremos actualizar.
    for drawing in doc.element.xpath('.//w:drawing'):
        # 4.1) Dentro de ese contenedor, <pic:pic> engloba la definición de la imagen:
        #      - Metadatos (cNvPr), estilos y referencia al binario.
        pics = drawing.xpath('.//pic:pic')
        if not pics:
            # No hay imagen en este drawing, saltar al siguiente nodo
            continue

        # 4.2) <pic:cNvPr> son las propiedades no visuales de la imagen:
        #      - Atributo 'descr' lo usamos como marcador para identificar placeholders.
        cNvPr = pics[0].xpath('.//pic:cNvPr')[0]
        if cNvPr.get('descr') != marker:
            # Si no coincide el descriptor, no es nuestro placeholder
            continue

        # 5) <a:blip> es el nodo DrawingML que apunta al recurso binario:
        #    <a:blip r:embed="rIdX"/> define qué imagen cargar
        blip = pics[0].xpath('.//a:blip')[0]
        # 5.1) Al actualizar r:embed con new_rId, le decimos a Word que use
        #      la imagen recién insertada en word/media/
        blip.set(qn('r:embed'), new_rId)

        # 6) <wp:extent> especifica el ancho (cx) y alto (cy) en EMU
        extent = drawing.xpath('.//wp:extent')[0]
        extent.set('cx', str(cx))  # ancho en EMU
        extent.set('cy', str(cy))  # alto en EMU

        # 7) Salir después de la primera coincidencia
        #    Solo queremos reemplazar un placeholder por llamada.
        break


def insertar_imagenes(doc, image_files, marker):
    """
    Propósito:
        Gestionar la inserción de una o varias imágenes en los placeholders del documento.
        Clona el placeholder original si se deben insertar múltiples archivos.

    Entradas:
        doc (docx.Document): Documento Word abierto en memoria.
        image_files (list[FileStorage]): Lista de imágenes subidas desde Flask.
        marker (str): Valor del atributo 'descr' en <pic:cNvPr> que identifica el placeholder.

    Salidas:
        None: Modifica el objeto `doc` directamente.

    Dependencias:
        - reemplazar_imagen_flotante: maneja la carga de bytes, generación de rId y actualización de XML.
        - deepcopy: permite clonar nodos XML para insertar múltiples instancias sin perder el original.
        - doc.element.xpath: busca nodos <w:drawing> que contienen los placeholders.
    """
    # 1) Buscar todos los contenedores <w:drawing> con el marker en <pic:cNvPr>
    drawings = [
        d for d in doc.element.xpath('.//w:drawing')  # obtiene lista de nodos <w:drawing>
        if d.xpath('.//pic:cNvPr')[0].get('descr') == marker  # filtra solo los que coinciden con marker
    ]
    #    Por qué: identificar todas las posiciones donde puede ir una imagen.
    #    Relación: estos nodos serán actualizados por reemplazar_imagen_flotante.
    if not drawings:
        # Por qué: si no encuentra placeholders, no hay nada que reemplazar.
        # Relación: evita llamar a reemplazar_imagen_flotante innecesariamente.
        return

    # 2) Seleccionar el primer placeholder como plantilla
    first = drawings[0]                # nodo XML <w:drawing> original
    #    Por qué: usamos el primer nodo para la primera imagen y como base para clonar.
    #    Relación: reemplazar_imagen_flotante siempre repara el primer placeholder.
    parent = first.getparent()         # contenedor XML de los drawings
    #    Por qué: necesitamos el nodo padre para insertar clones.
    #    Relación: parent.insert se usará para agregar nodos clonados.
    idx = parent.index(first)          # posición del placeholder original en `parent`
    #    Por qué: conocer el índice inicial permite calcular posición de inserción.
    #    Relación: idx + i determina dónde ubicar cada clon.

    # 3) Iterar sobre cada imagen subida
    for i, img in enumerate(image_files):  # i: índice (0,1,2...), img: objeto FileStorage
        # 3.1) Determinar nodo a usar: original si i=0, clon si i>0
        drawing = first if i == 0 else deepcopy(first)
        #      Por qué: el primer placeholder se actualiza directamente,
        #      y para más imágenes mantenemos la anterior intacta.
        #      Relación: deepcopy crea un nodo independiente para no interferir con el original.

        # 3.2) Reemplazar contenido y tamaño en el placeholder original
        reemplazar_imagen_flotante(doc, marker, img)
        #      Por qué: esta función maneja la inserción real del binario,
        #      generación de new_rId y ajuste de dimensiones.
        #      Relación: conecta image_files con <a:blip r:embed> y <wp:extent>.

        # 3.3) Insertar el clon tras el original si es imagen adicional
        if i > 0:
            parent.insert(idx + i, drawing)
            #      Por qué: ubicamos cada nueva imagen en orden de subida.
            #      Relación: mantiene la secuencia de <w:drawing> en el XML.

    # Fin de insertar_imagenes: cada img en image_files aparece en un <w:drawing> distinto

def replace_marker_with_text(doc, marker, text):
    for p in iter_paragraphs(doc):
        if marker in p.text:
            # Eliminar runs viejos
            for run in list(p.runs):
                p._p.remove(run._r)

            # Limpiar el texto del párrafo (por si queda el marcador)
            p.text = ''

            # Limpiar el texto de caracteres incompatibles con XML
            text = limpiar_texto_xml(str(text))

            # Crear run con el texto nuevo
            run = p.add_run(text)
            run.font.name = 'Arial'

            # Compatibilidad para fuentes
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')

            if marker == "{{proyecto}}":
                run.font.size = Pt(13)
                run.bold = True
                p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            else:
                # Para cliente, orden_compra, nota_venta
                run.font.size = Pt(11)
                run.bold = False
                p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT  # opcional, por defecto ya es izquierda

            return
        

# ====== Insertar texto en Word =======
def insertar_texto(doc, marker, texto, size_pt):
    """
    Busca celdas con `marker`, borra su contenido y agrega todo el `texto`
    línea a línea con la fuente y tamaño indicados.
    Devuelve la lista de párrafos creados (para más tarde resaltar).
    """
    paras = []

    # Limpiar el texto de caracteres incompatibles con XML
    texto = limpiar_texto_xml(texto)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if marker in cell.text:
                    cell.text = ''
                    para = cell.add_paragraph()
                    para.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                    for line in texto.split('\n'):
                        # Limpiar cada línea individualmente por seguridad
                        line = limpiar_texto_xml(line)
                        run = para.add_run(line)
                        aplicar_fuente_cascadia_code(run, size_pt)
                        para.add_run('\n')  # salto tras cada línea
                    paras.append(para)
    return paras

def insertar_info_dispositivo(doc, modelo, serial, version):
    # Limpiar los valores de caracteres incompatibles con XML
    modelo = limpiar_texto_xml(modelo) if modelo else ""
    serial = limpiar_texto_xml(serial) if serial else ""
    version = limpiar_texto_xml(version) if version else ""

    # También revisamos las celdas de todas las tablas en el documento, por si no están en párrafos
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if "{{modelo}}" in cell.text:
                    cell.text = cell.text.replace("{{modelo}}", modelo)
                    para = cell.paragraphs[0]
                    para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER  # Centrar texto
                    # Aplicar formato Arial 11 a todo el párrafo
                    for run in para.runs:
                        run.font.name = 'Arial'
                        run.font.size = Pt(11)
                        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')

                if "{{serial}}" in cell.text:
                    cell.text = cell.text.replace("{{serial}}", serial)
                    para = cell.paragraphs[0]
                    para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER  # Centrar texto
                    for run in para.runs:
                        run.font.name = 'Arial'
                        run.font.size = Pt(11)
                        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')

                if "{{version}}" in cell.text:
                    cell.text = cell.text.replace("{{version}}", version)
                    para = cell.paragraphs[0]
                    para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER  # Centrar texto
                    for run in para.runs:
                        run.font.name = 'Arial'
                        run.font.size = Pt(11)
                        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')

def procesar_archivo(file_stream, docx_template_path,img_1,img_2,img_3,proyecto,cliente,ordenCompra,notaVenta,file_type):

    # Carga la plantilla
    doc = Document(docx_template_path)

    # Leemos todo el contenido del TXT en 'lines'
    file_stream.seek(0)
    lines = file_stream.read().decode('utf-8').split('\n')

    # --------- EXTRACCION DE INFORMACION DEL DISPOSITIVO ----------
    # Inicializamos variables para almacenar información del dispositivo
    modelo, serial, version = None, None, None

    # Expresiones regulares para extraer información del dispositivo
    if file_type == 'SW L2 9200' or file_type == 'SW L2 9300' or file_type == 'SW L2 9500':
        # Ahora buscamos el bloque de "INICIO PRUEBA 1"
        patron_inicio_prueba_1 = re.compile(r'.*[#>]\s*INICIO\s+PRUEBA\s+1\b', re.IGNORECASE)
        # Expresiones regulares para extraer información del dispositivo
        modelo_regex = re.compile(r'Model Number\s*:\s*(\S+)', re.IGNORECASE)
        serial_regex = re.compile(r'System Serial Number\s*:\s*(\S+)', re.IGNORECASE)

        # Buscar información del dispositivo
        for line in lines:
            model_match = modelo_regex.search(line)
            serial_match = serial_regex.search(line)

            if model_match:
                modelo = model_match.group(1).strip()
            if serial_match:
                serial = serial_match.group(1).strip()

        for line in lines:
            match = patron_inicio_prueba_1.match(line.strip())
            if match:
                # Contenido dentro de prueba 1
                for siguiente_linea in lines[lines.index(line):]: #Comienza a buscar en las líneas siguientes a la línea actual (donde se encontró "INICIO PRUEBA 1") para encontrar la línea que contiene la versión.
                    version_match = re.search(r'Version\s+(\S+)', siguiente_linea, re.IGNORECASE) #Usa una expresión regular para buscar la línea que contiene "Version" y capturar el valor que le sigue.
                    if version_match:
                        version = version_match.group(1).strip()
                        break  # Salir del bucle al encontrar la versión
                break  # Salir del bucle principal al encontrar el bloque de prueba

    elif file_type == 'SW L3 9348GC' or file_type == 'SW L3 C93180YC':
        # Ahora buscamos el bloque de "INICIO PRUEBA 1"
        patron_inicio_prueba_1 = re.compile(r'.*[#>]\s*INICIO\s+PRUEBA\s+1\b', re.IGNORECASE)
        for line in lines:
            match = patron_inicio_prueba_1.match(line.strip())
            if match:
                # Contenido dentro de prueba 1
                for siguiente_linea in lines[lines.index(line) + 1:]:  # Comienza a buscar desde la siguiente línea
                    model_match = re.search(r'PID:\s*(\S+)', siguiente_linea, re.IGNORECASE)
                    serial_match = re.search(r'SN:\s*(\S+)', siguiente_linea, re.IGNORECASE)
                    version_match = re.search(r'NXOS:\s+version\s+(\S+)', siguiente_linea, re.IGNORECASE)

                    if model_match:
                        modelo = model_match.group(1).strip()
                    if serial_match:
                        serial = serial_match.group(1).strip()
                    if version_match:
                        version = version_match.group(1).strip()

                    # Verificar si se encontraron todos los datos
                    if modelo and serial and version:
                        break  # Salir del bucle si todos están encontrados
                break  # Salir del bucle principal al encontrar el bloque de prueba

    elif file_type == 'SW IE3300' or file_type == 'SW IE4010':
        # Ahora buscamos el bloque de "INICIO PRUEBA 1"
        patron_inicio_prueba_1 = re.compile(r'.*[#>]\s*INICIO\s+PRUEBA\s+1\b', re.IGNORECASE)

        # Expresiones regulares para extraer información del dispositivo
        modelo_regex = re.compile(r'Model Number\s*:\s*(\S+)', re.IGNORECASE)
        serial_regex = re.compile(r'System Serial Number\s*:\s*(\S+)', re.IGNORECASE)

        # Buscar información del dispositivo
        for line in lines:
            model_match = modelo_regex.search(line)
            serial_match = serial_regex.search(line)

            if model_match:
                modelo = model_match.group(1).strip()
            if serial_match:
                serial = serial_match.group(1).strip()

        for line in lines:
            match = patron_inicio_prueba_1.match(line.strip())
            if match:
                # Contenido dentro de prueba 1
                for siguiente_linea in lines[lines.index(line):]: #Comienza a buscar en las líneas siguientes a la línea actual (donde se encontró "INICIO PRUEBA 1") para encontrar la línea que contiene la versión.
                    version_match = re.search(r'Version\s+(\S+)', siguiente_linea, re.IGNORECASE) #Usa una expresión regular para buscar la línea que contiene "Version" y capturar el valor que le sigue.
                    if version_match:
                        version = version_match.group(1).strip()
                        break  # Salir del bucle al encontrar la versión
                break  # Salir del bucle principal al encontrar el bloque de prueba
    
    elif file_type == 'Router C8500' or file_type == 'Router ISR4431':
        # Ahora buscamos el bloque de "INICIO PRUEBA 1"
        patron_inicio_prueba_1 = re.compile(r'.*[#>]\s*INICIO\s+PRUEBA\s+1\b', re.IGNORECASE)
        for line in lines:
            match = patron_inicio_prueba_1.match(line.strip())
            if match:
                # Contenido dentro de prueba 1
                for siguiente_linea in lines[lines.index(line) + 1:]:  # Comienza a buscar desde la siguiente línea
                    model_match = re.search(r'PID:\s*(\S+)', siguiente_linea, re.IGNORECASE)
                    serial_match = re.search(r'SN:\s*(\S+)', siguiente_linea, re.IGNORECASE)

                    if model_match:
                        modelo = model_match.group(1).strip()
                    if serial_match:
                        serial = serial_match.group(1).strip()

                    # Verificar si se encontraron todos los datos
                    if modelo and serial:
                        break  # Salir del bucle si todos están encontrados
                break  # Salir del bucle principal al encontrar el bloque de prueba

        for line in lines:
            match = patron_inicio_prueba_1.match(line.strip())
            if match:
                # Contenido dentro de prueba 1
                for siguiente_linea in lines[lines.index(line):]: #Comienza a buscar en las líneas siguientes a la línea actual (donde se encontró "INICIO PRUEBA 1") para encontrar la línea que contiene la versión.
                    version_match = re.search(r'Version\s+(\S+)', siguiente_linea, re.IGNORECASE) #Usa una expresión regular para buscar la línea que contiene "Version" y capturar el valor que le sigue.
                    if version_match:
                        version = version_match.group(1).strip()
                        break  # Salir del bucle al encontrar la versión
                break  # Salir del bucle principal al encontrar el bloque de prueba

    elif file_type == 'AP C9115AXI' or file_type == 'AP C9120AXE' or file_type == 'AP C9130AXI':
        # Expresiones regulares para extraer información del dispositivo
        modelo_regex = re.compile(r'Product/Model Number\s*:\s*(\S+)', re.IGNORECASE)
        serial_regex = re.compile(r'Top Assembly Serial Number\s*:\s*(\S+)', re.IGNORECASE)
        version_regex = re.compile(r'Primary Boot Image\s*:\s*(\S+)', re.IGNORECASE)

        # Buscar información del dispositivo
        for line in lines:
            model_match = modelo_regex.search(line)
            serial_match = serial_regex.search(line)
            version_match = version_regex.search(line)

            if model_match:
                modelo = model_match.group(1).strip()
            if serial_match:
                serial = serial_match.group(1).strip()
            if version_match:
                version = version_match.group(1).strip()

    elif file_type == 'AP C9115AXI' or file_type == 'AP C9120AXE' or file_type == 'AP C9130AXI':
        # Expresiones regulares para extraer información del dispositivo
        modelo_regex = re.compile(r'Product/Model Number\s*:\s*(\S+)', re.IGNORECASE)
        serial_regex = re.compile(r'Top Assembly Serial Number\s*:\s*(\S+)', re.IGNORECASE)
        version_regex = re.compile(r'Primary Boot Image\s*:\s*(\S+)', re.IGNORECASE)

        # Buscar información del dispositivo
        for line in lines:
            model_match = modelo_regex.search(line)
            serial_match = serial_regex.search(line)
            version_match = version_regex.search(line)

            if model_match:
                modelo = model_match.group(1).strip()
            if serial_match:
                serial = serial_match.group(1).strip()
            if version_match:
                version = version_match.group(1).strip()

    elif file_type == 'Check Point 6200' or file_type == 'Check Point 6600':
        # Expresiones regulares para extraer información del dispositivo
        modelo_regex = re.compile(r'Appliance Name\s*:\s*(.+)', re.IGNORECASE)  # Captura todo lo que sigue
        serial_regex = re.compile(r'Appliance SN\s*:\s*(\S+)', re.IGNORECASE)
        version_regex = re.compile(r'SVN Foundation Version String\s*:\s*(\S+)', re.IGNORECASE)

        # Buscar información del dispositivo
        for line in lines:
            model_match = modelo_regex.search(line)
            serial_match = serial_regex.search(line)
            version_match = version_regex.search(line)

            if model_match:
                modelo = model_match.group(1).strip()
            if serial_match:
                serial = serial_match.group(1).strip()
            if version_match:
                version = version_match.group(1).strip()

    # Insertar información del dispositivo en el documento
    insertar_info_dispositivo(doc, modelo, serial, version)


    # -------------PRUEBAS--------------
    # 1) Primero, buscamos cuántas "pruebas" hay en el texto. 
    #    Cada instrucción de inicio de prueba debería tener formato:
    #       # INICIO PRUEBA {numero}
    #   Extraemos todos los números que aparezcan en esas líneas.
    patron_inicio_any = re.compile(r'.*[#>]\s*INICIO\s+PRUEBA\s+(\d+)\b', re.IGNORECASE)
    numeros_encontrados = set()

    for line in lines:
        match = patron_inicio_any.match(line.strip())
        if match:
            numeros_encontrados.add(int(match.group(1)))

    buffer = BytesIO()
    if not numeros_encontrados:
        doc.save(buffer)
        buffer.seek(0)
        nombre = f'{file_type}_documento_vacio.docx'
        return buffer, nombre

    # 2) Ordenamos los números de prueba (1, 2, 3, ...)
    numeros_ordenados = sorted(numeros_encontrados)
    # 3) Por cada número de prueba, construimos los regex de inicio y fin,
    #    llamamos a 'pruebas' para extraer el bloque, y luego insertamos el texto
    contador=0
    for n in numeros_ordenados:
        # Creamos un patrón para:    # INICIO PRUEBA {n}
        start_re = re.compile(rf'.*[#>]\s*INICIO\s+PRUEBA\s+{n}\b', re.IGNORECASE)
        # Creamos un patrón para:    # FIN PRUEBA {n}
        end_re = re.compile(rf'.*[#>]\s*FIN\s+PRUEBA\s+{n}\b', re.IGNORECASE)

        # Extraemos el bloque correspondiente a esa prueba 
        bloques = pruebas(lines, start_re, end_re)

        # Si encontramos bloques, los procesamos uno a uno.
        # El texto a insertar lleva un sufijo con dos dígitos, p. ej. "01", "02", ...
        sufijo = f"{n:02d}"
        texto_label = f"Insertar codigo de la extracción {sufijo}"
        
        for bloque in bloques:
            contador= n
            #Se inserta el texto
            paras = insertar_texto(doc,texto_label,bloque,8)
            #Se subraya el texto
            subrayar_texto(paras,file_type,contador)

    # Se insertan las imagenes
    # Se reemplazan las imágenes flotantes predefinidas
    insertar_imagenes(doc, img_1, 'IMG1')
    insertar_imagenes(doc, img_2, 'IMG2')
    insertar_imagenes(doc, img_3, 'IMG3')
    replace_marker_with_text(doc, "{{proyecto}}", proyecto)
    replace_marker_with_text(doc, "{{cliente}}", cliente)
    replace_marker_with_text(doc, "{{orden_compra}}", ordenCompra)
    replace_marker_with_text(doc, "{{nota_venta}}", notaVenta)
    # 4) Una vez terminadas todas las pruebas, guardamos el documento
    doc.save(buffer)
    buffer.seek(0)
    nombre = f'{modelo} {serial}.docx'
    return buffer, nombre


def suscripcion_vigente(user):
    """
    Propósito:
        Determinar si la suscripción del usuario está actualmente vigente,
        es decir, si está en estado ACTIVA y la fecha de fin aún no ha vencido.

    Entradas:
        - user: instancia del modelo User que contiene, entre otros,
          los campos estado_suscripcion y fecha_fin_suscripcion.

    Salidas:
        - bool: True si la suscripción está activa y no vencida,
          False en cualquier otro caso.

    Dependencias:
        - Campo user.estado_suscripcion (string).
        - Campo user.fecha_fin_suscripcion (date o None).
        - datetime.utcnow().date() para obtener la fecha actual.
    """

    # Si no hay usuario (None o similar), no puede tener suscripción vigente.
    if not user:
        return False

    # Verificamos si el estado de suscripción del usuario es exactamente 'ACTIVA'.
    esta_activa = user.estado_suscripcion == 'ACTIVA'

    # Verificamos que exista una fecha de fin de suscripción (no sea None).
    tiene_fecha_fin = bool(user.fecha_fin_suscripcion)

    # Obtenemos la fecha de hoy en UTC, sin componente de hora.
    hoy_utc = datetime.utcnow().date()

    # Comprobamos que la fecha de fin sea hoy o una fecha futura (no esté vencida).
    no_esta_vencida = tiene_fecha_fin and user.fecha_fin_suscripcion >= hoy_utc

    # Devolvemos True solo si está activa y no ha vencido; en caso contrario, False.
    return esta_activa and no_esta_vencida



def necesita_pago(user):
    """
    Propósito:
        Indicar si el usuario se encuentra en un estado de suscripción que
        requiere pasar por el flujo de pago / checkout de Mercado Pago.

    Entradas:
        - user: instancia del modelo User con el campo estado_suscripcion.

    Salidas:
        - bool: True si debe ir a la pasarela de pago, False si no.

    Dependencias:
        - Campo user.estado_suscripcion (string).
        - Conjunto de estados definidos como "requiere pago".
    """

    # Definimos el conjunto de estados que consideramos que necesitan pago.
    estados_que_necesitan_pago = {
        'SIN_SUSCRIPCION',  # Nunca ha contratado un plan.
        'PENDIENTE_MP',     # Ya inició el proceso en MP pero aún no se autorizó.
        'PAUSADA',          # La suscripción está pausada en MP.
        'CANCELADA',        # La suscripción fue cancelada.
        'VENCIDA',          # La fecha de fin de suscripción ya pasó.
        'EN_GRACIA',        # Periodo de gracia, pero aún queremos forzar pago.
    }

    # Devolvemos True si el estado actual del usuario está en el conjunto anterior.
    return user.estado_suscripcion in estados_que_necesitan_pago

def suscripcion_requerida(vista):
    """
    Propósito:
        Decorador para vistas de Flask que obliga a que el usuario:
        1. Esté autenticado (logueado), y
        2. Tenga una suscripción vigente.

    Entradas:
        vista: función de vista de Flask que queremos proteger
               (por ejemplo: upload_files, dashboard, etc.).

    Salidas:
        Devuelve una nueva función (vista_protegida) que envuelve a vista
        y agrega la lógica de:
            - verificar login
            - verificar suscripción
            - redirigir si no cumple

    Dependencias:
        - @login_required: decorador de Flask-Login que exige usuario autenticado.
        - current_user: objeto de Flask-Login que representa al usuario actual.
        - suscripcion_vigente(user): función tuya que devuelve True/False.
        - flash: función de Flask para mostrar mensajes al usuario.
        - redirect, url_for: funciones de Flask para redirigir a otra ruta.
    """

    # Hace que vista_protegida conserve el nombre y metadatos de vista original,
    # como si siguiera siendo la misma función a ojos de Flask y las herramientas.
    @wraps(vista)

    # Este decorador de Flask-Login fuerza SOLO usuarios logueados
    @login_required
    def vista_protegida(*args, **kwargs):

        # Si el usuario actual NO tiene una suscripción vigente...
        if not suscripcion_vigente(current_user):
            # Mostramos un mensaje de advertencia en la interfaz (con Flash).
            flash(
                'Necesitas una suscripción ACTIVA para acceder a esta sección.',
                'warning'
            )

            # Redirigimos al usuario a la ruta donde puede pagar/activar
            # su suscripción
            return redirect(url_for('suscripcion_checkout'))

        # Si tiene suscripción vigente, ejecutamos la vista original
        # con sus mismos argumentos (*args, **kwargs) y retornamos su resultado.
        return vista(*args, **kwargs)

    # devolvemos la función "envuelta" (vista_protegida)
    return vista_protegida


def extraer_evento_mp(body, query):
    # Propósito:
    #   A partir del body (JSON) y de la query string del webhook de Mercado Pago,
    #   obtener el "tipo" de evento (topic) y el "id" del recurso principal.
    #
    # Entradas:
    #   body  -> diccionario con el JSON del webhook.
    #   query -> diccionario con los parámetros de la URL (?type=..., data.id=...).
    #
    # Salidas:
    #   (topic, resource_id) -> tupla de dos strings, o (None, None) si no se puede.
    #
    # Dependencias:
    #   Solo usa tipos básicos de Python (dict, str), no requiere imports extra.

    # Intentamos obtener el tipo de evento directamente desde el body.
    topic = body.get("type")

    # Si en el body no vino "type", probamos tomarlo desde la query string.
    if topic is None:
        topic = query.get("type")

    # Obtenemos el campo "data" del body, si existe, o un diccionario vacío.
    data_dict = body.get("data") or {}

    # Dentro de "data", intentamos leer el identificador principal del recurso.
    resource_id = data_dict.get("id")

    # Si no encontramos el id dentro de "data", probamos con "data.id" en la query.
    if resource_id is None:
        resource_id = query.get("data.id")

    # Como último intento, miramos si hay un "id" en la raíz del body.
    if resource_id is None:
        resource_id = body.get("id")

    # Si falta el topic o el id del recurso, devolvemos (None, None) para indicar error.
    if topic is None or resource_id is None:
        return None, None

    # Devolvemos la tupla (topic, resource_id) cuando ambos existen.
    return topic, resource_id


def obtener_usuario_desde_preapproval(preapproval):
    # Propósito:
    #   Dado un objeto "preapproval" de Mercado Pago, encontrar el usuario
    #   en nuestra base de datos usando, en este orden:
    #       1) external_reference con formato "user:<id>".
    #       2) el campo mp_preapproval_id guardado en el modelo User.
    #
    # Entradas:
    #   preapproval -> diccionario que representa la suscripción en Mercado Pago.
    #
    # Salidas:
    #   Instancia de User si se encuentra, o None en caso contrario.
    #
    # Dependencias:
    #   - Modelo User (from models import User).
    #   - Campo mp_preapproval_id en la tabla de usuarios.

    # Intentamos leer el external_reference definido cuando se creó la suscripción.
    external_reference = preapproval.get("external_reference")

    # Inicializamos user en None para ir actualizándolo si encontramos coincidencias.
    user = None

    # Verificamos si external_reference existe y comienza con el prefijo esperado.
    if external_reference and external_reference.startswith("user:"):
        # Separamos el texto después de "user:" para obtener el id en formato string.
        parte_id = external_reference.split(":", 1)[1]
        try:
            # Convertimos la parte numérica del string a un entero.
            user_id = int(parte_id)
            # Buscamos en la base de datos al usuario con esa clave primaria.
            user = User.query.get(user_id)
        except ValueError:
            # Si no se puede convertir a entero, ignoramos este método y seguimos.
            user = None

    # Si todavía no encontramos usuario, probamos buscar por mp_preapproval_id.
    if user is None:
        # Obtenemos el id de la suscripción desde el objeto preapproval.
        preapproval_id = preapproval.get("id")
        # Si existe un id, buscamos un usuario que lo tenga guardado.
        if preapproval_id:
            user = User.query.filter_by(mp_preapproval_id=preapproval_id).first()

    # Devolvemos el usuario encontrado o None si no hubo coincidencias.
    return user


# ====== RUTAS ======

@app.route('/')
def landing():
    """
    Landing page con información del proyecto.

    Lógica:
    - No autenticado -> muestra landing.
    - Autenticado + suscripción ACTIVA -> redirige a /app.
    - Autenticado + sin suscripción vigente -> se queda en landing
      (desde aquí puede ir a /suscripcion, logout, etc.).
    """
    if current_user.is_authenticated:
        if suscripcion_vigente(current_user):
            return redirect(url_for('upload_files'))
        # Si está autenticado pero NO tiene suscripción vigente,
        # simplemente mostramos la landing.
        # Así el botón "Volver" de suscripción puede traerte aquí sin bucles.

    return render_template('landing.html')




@app.route('/terminos')
def terminos():
    """Página de términos y condiciones"""
    return render_template('terminos.html')


@app.route('/sobre-nosotros')
def sobre_nosotros():
    """Página sobre nosotros"""
    return render_template('sobre_nosotros.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Propósito:
        Registrar nuevos usuarios en la aplicación usando un email único y
        almacenando la contraseña de forma segura (hasheada desde el modelo User).

    Entradas:
        - Método GET:
            * Muestra el formulario de registro.
        - Método POST (formulario):
            * email: correo electrónico del usuario.
            * password: contraseña elegida por el usuario.
            * confirm_password: repetición de la contraseña.
            * nombre: nombre del usuario (opcional).
            * apellido: apellido del usuario (opcional).

    Salidas:
        - Renderiza 'register.html' cuando:
            * Es una petición GET.
            * Falta información o hay errores de validación.
        - Redirige a 'login' cuando:
            * El registro se completa correctamente.

    Dependencias:
        - validate_email_format para validar y normalizar el correo.
        - validate_password_strength para comprobar la fortaleza de la contraseña.
        - Modelo User para crear el registro en la base de datos.
        - db.session para guardar el nuevo usuario.
        - current_user para saber si ya hay alguien autenticado.
    """

    # Comprobamos si ya hay un usuario autenticado en la sesión actual.
    if current_user.is_authenticated:
        # Si ya está logueado, no tiene sentido registrar otro usuario; lo mandamos a la app.
        return redirect(url_for('upload_files'))

    # Revisamos si la petición es de tipo POST (envío del formulario de registro).
    if request.method == 'POST':
        # Obtenemos el email del formulario y quitamos espacios extra al inicio y final.
        email = request.form.get('email', '').strip()
        # Obtenemos la contraseña tal como fue ingresada por el usuario.
        password = request.form.get('password')
        # Obtenemos la confirmación de la contraseña.
        confirm_password = request.form.get('confirm_password')
        # Obtenemos el nombre, opcional, y eliminamos espacios sobrantes.
        nombre = request.form.get('nombre', '').strip()
        # Obtenemos el apellido, opcional, y eliminamos espacios sobrantes.
        apellido = request.form.get('apellido', '').strip()

        # Validamos que se haya ingresado un email y una contraseña.
        if not email or not password:
            # Mostramos un mensaje de error indicando que ambos campos son obligatorios.
            flash('Email y contraseña son obligatorios', 'danger')
            # Volvemos a mostrar el formulario de registro.
            return render_template('register.html')

        # Comprobamos que el correo no exceda el máximo permitido (150 caracteres).
        if len(email) > 150:
            # Si es demasiado largo, mostramos un mensaje de error.
            flash('El correo no puede exceder 150 caracteres', 'danger')
            # Renderizamos de nuevo el formulario para que pueda corregirlo.
            return render_template('register.html')

        # Si el usuario escribió un nombre, revisamos que no sea demasiado largo.
        if nombre and len(nombre) > 80:
            # Mostramos error si el nombre supera los 80 caracteres.
            flash('El nombre no puede exceder 80 caracteres', 'danger')
            # Volvemos a mostrar el formulario.
            return render_template('register.html')

        # Si el usuario escribió un apellido, revisamos que no sea demasiado largo.
        if apellido and len(apellido) > 80:
            # Mostramos error si el apellido supera los 80 caracteres.
            flash('El apellido no puede exceder 80 caracteres', 'danger')
            # Volvemos a mostrar el formulario.
            return render_template('register.html')

        # Llamamos a la función que valida y normaliza el correo electrónico.
        is_valid_email, normalized_email, email_error = validate_email_format(email)
        # Si el correo no pasa la validación de formato, mostramos el motivo.
        if not is_valid_email:
            # Mostramos el mensaje de error específico que devuelve la función.
            flash(f'Correo inválido: {email_error}', 'danger')
            # Volvemos a mostrar el formulario de registro.
            return render_template('register.html')

        # Comparamos la contraseña con la confirmación para asegurarnos de que coincidan.
        if password != confirm_password:
            # Si no son iguales, informamos al usuario del error.
            flash('Las contraseñas no coinciden', 'danger')
            # Renderizamos de nuevo el formulario para que las vuelva a ingresar.
            return render_template('register.html')

        # Llamamos a la función que evalúa la fortaleza de la contraseña.
        is_valid_password, password_error = validate_password_strength(password)
        # Si la contraseña no cumple los requisitos, mostramos el motivo.
        if not is_valid_password:
            # Mostramos el mensaje de error devuelto por la validación.
            flash(password_error, 'danger')
            # Volvemos a mostrar el formulario de registro.
            return render_template('register.html')

        # Buscamos si ya existe un usuario con ese correo normalizado en la base de datos.
        if User.query.filter_by(email=normalized_email).first():
            # Si ya hay un registro con ese correo, no permitimos un duplicado.
            flash('El correo ya está registrado', 'danger')
            # Mostramos otra vez el formulario para que use otro correo.
            return render_template('register.html')

        # Creamos una nueva instancia de User con los datos ingresados.
        # El modelo se encargará de hashear la contraseña internamente.
        new_user = User(
            email=normalized_email,
            password=password,
            nombre=nombre,
            apellido=apellido
        )

        # Añadimos el nuevo usuario a la sesión de la base de datos.
        db.session.add(new_user)
        # Confirmamos los cambios guardando el nuevo registro en la base.
        db.session.commit()

        # Mostramos un mensaje indicando que el registro fue exitoso.
        flash('Registro exitoso. Inicia sesión.', 'success')
        # Redirigimos al usuario a la página de login para que pueda iniciar sesión.
        return redirect(url_for('login'))

    # Si la petición es GET (o no se cumplió ninguna condición anterior), mostramos el formulario.
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Propósito:
        Autenticar usuarios, manejar el inicio de sesión y registrar el último acceso.
        Además, redirigir a la página de suscripción si el usuario no tiene una
        suscripción vigente y necesita pagar.

    Entradas:
        - Método GET:
            * Muestra el formulario de inicio de sesión.
        - Método POST (formulario):
            * email: correo del usuario.
            * password: contraseña del usuario.

    Salidas:
        - Renderiza la plantilla 'login.html' cuando:
            * Es un GET.
            * Faltan datos.
            * Las credenciales son incorrectas.
            * La cuenta no está activa.
        - Redirige a:
            * /suscripcion si necesita pagar.
            * /app (upload_files) si la suscripción está vigente.
            * next (si viene de una página protegida) tras login exitoso.

    Dependencias:
        - Modelo User y db.session para consultar y actualizar la BD.
        - Flask-Login: current_user, login_user.
        - Funciones suscripcion_vigente(user) y necesita_pago(user) para la lógica de suscripción.
        - datetime.utcnow para registrar el último acceso.
    """

    # Verificamos si ya hay un usuario autenticado en la sesión actual.
    if current_user.is_authenticated:
        # Revisamos si su suscripción NO está vigente y además requiere pago.
        if not suscripcion_vigente(current_user) and necesita_pago(current_user):
            # Si debe pagar, lo redirigimos a la página de suscripción.
            return redirect(url_for('suscripcion_checkout'))
        # Si la suscripción está bien o no necesita pago, lo mandamos a la app principal.
        return redirect(url_for('upload_files'))

    # Comprobamos si la petición es de tipo POST (envío del formulario).
    if request.method == 'POST':
        # Obtenemos el correo desde el formulario y eliminamos espacios extra.
        email = request.form.get('email', '').strip()
        # Obtenemos la contraseña desde el formulario tal como viene.
        password = request.form.get('password')
        # Obtenemos el valor del checkbox "remember" (puede venir como 'on' o no venir).
        remember = request.form.get('remember', False)

        # Verificamos que el correo y la contraseña no estén vacíos.
        if not email or not password:
            # Mostramos un mensaje de error si faltan datos.
            flash('Correo y contraseña son requeridos', 'danger')
            # Renderizamos de nuevo la plantilla de login para que intente otra vez.
            return render_template('login.html')

        # Buscamos en la base de datos un usuario con ese correo electrónico.
        user = User.query.filter_by(email=email).first()

        # Verificamos que el usuario exista y que la contraseña sea correcta.
        if user and user.check_password(password):
            # Comprobamos si la cuenta del usuario está marcada como ACTIVA.
            if user.estado_cuenta != 'ACTIVA':
                # Si la cuenta no está activa, mostramos un mensaje y no iniciamos sesión.
                flash('Tu cuenta no está activa', 'danger')
                # Volvemos a mostrar el formulario de login.
                return render_template('login.html')

            # Llamamos a login_user para guardar al usuario en la sesión.
            login_user(user, remember=remember)
            # Actualizamos el campo ultimo_acceso con la fecha y hora actual en UTC.
            user.ultimo_acceso = datetime.utcnow()
            # Guardamos los cambios en la base de datos.
            db.session.commit()

            # Revisamos si la suscripción NO está vigente y además requiere pago.
            if not suscripcion_vigente(user) and necesita_pago(user):
                # Si debe pagar, lo redirigimos a la página de suscripción.
                return redirect(url_for('suscripcion_checkout'))

            # Obtenemos la página a la que quería ir originalmente (si existe).
            next_page = request.args.get('next')
            # Si existe next_page, redirigimos allí; si no, vamos a la app principal.
            return redirect(next_page) if next_page else redirect(url_for('upload_files'))

        else:
            # Si el usuario no existe o la contraseña es incorrecta, mostramos un mensaje de error.
            flash('Correo o contraseña incorrectos', 'danger')

    # Si es una petición GET, o hubo un error, mostramos el formulario de login.
    return render_template('login.html')



@app.route('/suscripcion')
@login_required
def suscripcion_checkout():
    # Propósito:
    #   Mostrar la página con la información del plan de suscripción
    #   y un botón para iniciar el proceso con Mercado Pago.
    #
    # Entradas:
    #   Ninguna directa (usa current_user solo para validar acceso).
    #
    # Salidas:
    #   Render del template 'suscripcion.html' con datos del plan.
    #
    # Dependencias:
    #   - current_user de Flask-Login (para validar acceso).
    #   - Template 'suscripcion.html'.

    # Definimos los datos básicos del plan que se mostrará en la página.
    if suscripcion_vigente(current_user):
        # Ya está al día, mejor mandarlo a la app
        return redirect(url_for('upload_files'))
    
    plan = {
        "nombre": "Plan Standard FAT Testing",
        "monto": 150000,
        "moneda": "CLP",
        "renovacion": "Mensual",
    }

    # Calculamos la fecha estimada de próxima renovación (por ahora, la fecha de hoy).
    proxima_fecha = datetime.utcnow().date()

    # Esta ruta interna creará la suscripción vía SDK y luego redirigirá a Mercado Pago.
    checkout_url = url_for('iniciar_suscripcion_mp')

    # Renderizamos el template de suscripción con los datos del plan y la URL del botón.
    return render_template('suscripcion.html', plan=plan, proxima_fecha=proxima_fecha, checkout_url=checkout_url)



@app.route('/suscripcion/iniciar')
@login_required
def iniciar_suscripcion_mp():
    # Obtenemos el SDK de Mercado Pago desde la configuración global.
    sdk = Config.sdk_mp

    # Construimos el external_reference con el id del usuario actual.
    external_reference = f"user:{current_user.id}"

    # Obtenemos el correo del payer.
    # En sandbox: usamos MP_TEST_PAYER_EMAIL si existe.
    # Si no está definido, usamos el correo del usuario.
    payer_email = os.environ.get("MP_TEST_PAYER_EMAIL", current_user.email)

    # Preparamos los datos del preapproval usando el esquema de Checkout MP.
    preapproval_data = {
        "auto_recurring": {
            "currency_id": "CLP",
            "transaction_amount": 150000,
            "frequency": 1,
            "frequency_type": "months",
        },
        "back_url": url_for("upload_files", _external=True),
        "external_reference": external_reference,
        "payer_email": payer_email,
        "reason": "Plan Standard FAT Testing",
    }

    # Inicializamos variables para usar después de llamar a la API.
    preapproval_id = None
    init_point = None

    # Intentamos crear la suscripción en Mercado Pago dentro de un bloque try/except.
    try:
        # Llamamos a la API de Mercado Pago para crear la suscripción.
        response = sdk.preapproval().create(preapproval_data)

        # Mostramos la respuesta cruda de Mercado Pago para depurar en caso de error.
        print("[MP] Respuesta completa al crear preapproval:", response)

        # Obtenemos el diccionario de respuesta principal.
        preapproval = response.get("response", {})

        # Extraemos el id de la suscripción creada.
        preapproval_id = preapproval.get("id")

        # Extraemos la URL donde se debe redirigir al usuario para completar la suscripción.
        init_point = preapproval.get("init_point") or preapproval.get("sandbox_init_point")

        # Mostramos en consola algo de información para depuración.
        print(f"[MP] preapproval creado: id={preapproval_id}, init_point={init_point}")

    except Exception as e:
        # Si ocurre un error al hablar con Mercado Pago, lo mostramos en consola.
        print(f"[MP] Error al crear preapproval: {e}")
        # Mostramos un mensaje de error al usuario.
        flash("Ocurrió un problema al iniciar la suscripción. Intenta de nuevo.", "danger")
        # Redirigimos de vuelta a la página de suscripción.
        return redirect(url_for("suscripcion_checkout"))

    # Verificamos si realmente obtuvimos un id de suscripción.
    if preapproval_id:
        # Guardamos el id de Mercado Pago en el usuario actual para futuras referencias.
        current_user.mp_preapproval_id = preapproval_id
        # Marcamos el estado de la suscripción como pendiente de confirmación en Mercado Pago.
        current_user.estado_suscripcion = "PENDIENTE_MP"
        # Guardamos los cambios en la base de datos.
        db.session.commit()
    else:
        # Si no hay id en la respuesta, registramos esto en la consola para depuración.
        print("[MP] La respuesta de preapproval no contiene 'id'.")
        # Mostramos un mensaje al usuario indicando que hubo un problema.
        flash("No se pudo crear la suscripción en Mercado Pago.", "danger")
        # Redirigimos nuevamente a la página de suscripción.
        return redirect(url_for("suscripcion_checkout"))

    # Si no se obtuvo una URL de checkout, no podemos continuar con el flujo normal.
    if not init_point:
        # Informamos por consola que falta la URL de redirección.
        print("[MP] La respuesta de preapproval no trae init_point.")
        # Informamos al usuario con un mensaje amigable.
        flash("No se pudo obtener la URL de pago de Mercado Pago.", "danger")
        # Redirigimos a la página de suscripción.
        return redirect(url_for("suscripcion_checkout"))

    # Si todo salió bien, redirigimos al usuario al checkout de Mercado Pago.
    return redirect(init_point)


@app.route('/mp/webhook', methods=['GET', 'POST'])
def mp_webhook():
    # Propósito:
    #   Recibir las notificaciones (webhooks) de Mercado Pago tanto reales como
    #   las de prueba del simulador, imprimir lo que llega y, si es un evento
    #   de suscripción, consultar la API para actualizar el estado del usuario.
    #
    # Entradas:
    #   - Método GET: usado por algunas pruebas / healthchecks → solo log y 200.
    #   - Método POST: notificaciones reales de Mercado Pago con body JSON.
    #
    # Salidas:
    #   - Siempre devuelve 200 OK para que Mercado Pago considere el webhook
    #     como recibido, aunque internamente algo falle.
    #
    # Dependencias:
    #   - request, json (de Flask).
    #   - extraer_evento_mp, obtener_usuario_desde_preapproval.
    #   - Config.sdk_mp, User, db, datetime, timedelta.

    # --- 1) Si llega un GET (simulador / prueba simple) ---
    # Si el método HTTP es GET, solo registramos la llamada y devolvemos 200.
    if request.method == "GET":
        # Imprimimos el método y los parámetros de la query para depurar.
        print("=== WEBHOOK MP (GET) ===")
        print("Query:", request.args.to_dict())
        print("========================")
        # Respondemos con 200 OK sin procesar nada más.
        return "", 200

    # --- 2) Aquí manejamos solo los POST (notificaciones reales) ---
    try:
        # Obtenemos el body del webhook como diccionario (puede venir vacío).
        body = request.get_json(silent=True) or {}
        # Obtenemos los parámetros de la query string (?type=..., data.id=..., etc.).
        query = request.args.to_dict()

        # Imprimimos todo el contenido del webhook para depuración.
        print("=== WEBHOOK MP (POST) ===")
        print("Query:", query)
        print("Body:", json.dumps(body, indent=2, ensure_ascii=False))
        print("=========================")

        # Obtenemos el tipo de evento (topic) y el id del recurso (resource_id).
        topic, resource_id = extraer_evento_mp(body, query)

        # Mostramos qué tipo de evento y cuál es el id asociado.
        print(f"[MP] topic={topic}, resource_id={resource_id}")

        # Obtenemos el SDK de Mercado Pago desde la configuración global.
        sdk = Config.sdk_mp

        # Si el evento corresponde a una suscripción (preapproval).
        if topic == "subscription_preapproval" and resource_id:
            try:
                # Consultamos la API de MP para obtener la suscripción completa.
                response = sdk.preapproval().get(resource_id)
                preapproval = response.get("response", {})

                # Mostramos en consola el preapproval recibido.
                print(f"[MP] preapproval recibido en webhook: {preapproval}")

                # Usamos el helper para encontrar al usuario en nuestra base.
                user = obtener_usuario_desde_preapproval(preapproval)

                # Si no encontramos usuario, lo registramos y terminamos.
                if user is None:
                    print(f"[MP] No se encontró usuario para preapproval {resource_id}.")
                else:
                    # Obtenemos el estado de la suscripción en MP.
                    status = preapproval.get("status")
                    # Obtenemos la fecha actual en UTC (solo fecha).
                    hoy = datetime.utcnow().date()
                    # Obtenemos el id real de la suscripción.
                    preapproval_id_real = preapproval.get("id")

                    # Mostramos un resumen en consola.
                    print(f"[MP] status={status}, preapproval_id={preapproval_id_real}, user_id={user.id}")

                    # Si la suscripción está autorizada, la marcamos como ACTIVA.
                    if status == "authorized":
                        user.estado_suscripcion = "ACTIVA"
                        if user.fecha_fin_suscripcion is None or user.fecha_fin_suscripcion < hoy:
                            user.fecha_fin_suscripcion = hoy + timedelta(days=30)
                        if preapproval_id_real:
                            user.mp_preapproval_id = preapproval_id_real

                    # Si está pausada, la marcamos como PAUSADA.
                    elif status == "paused":
                        user.estado_suscripcion = "PAUSADA"

                    # Si está cancelada, la marcamos como CANCELADA.
                    elif status == "cancelled":
                        user.estado_suscripcion = "CANCELADA"

                    # Para otros estados, solo los registramos.
                    else:
                        print(f"[MP] Status de preapproval no manejado aún: {status}")

                    # Guardamos los cambios en la base de datos.
                    db.session.commit()
                    print("[MP] Suscripción de usuario actualizada correctamente.")

            except Exception as e:
                # Mostramos el error en consola para poder depurarlo luego.
                print(f"[MP] Error procesando subscription_preapproval: {e}")

        # Si el tipo de evento no es de suscripción, por ahora solo lo registramos.
        else:
            print(f"[MP] Topic no manejado todavía o resource_id vacío: topic={topic}, resource_id={resource_id}")

    except Exception as e:
        # Cualquier error inesperado lo capturamos para que igual devolvamos 200.
        print(f"[MP] Error general en mp_webhook: {e}")

    # Siempre respondemos con 200 OK para que Mercado Pago considere el webhook como recibido.
    return "", 200

@app.route('/logout')
@login_required
def logout():
    """Ruta para cerrar sesión"""
    from flask_login import logout_user
    logout_user()
    flash('Has cerrado sesión exitosamente', 'info')
    return redirect(url_for('landing'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Propósito: generar token de recuperación y enviar correo.
    Entradas (POST form): email.
    Salidas: render de formulario o redirect a login tras mostrar mensaje.
    Dependencias: User, PasswordResetToken, send_password_reset_email, db.session.
    """
    # Generar token de recuperación y enviar correo
    if current_user.is_authenticated:
        return redirect(url_for('upload_files'))  # Evita que un usuario logueado pida reset

    if request.method == 'POST':
        email = request.form.get('email', '').strip()  # Correo para recuperar

        if not email:
            flash('Ingresa tu correo', 'danger')
            return render_template('forgot_password.html')

        is_valid_email, normalized_email, email_error = validate_email_format(email)  # Valida formato
        if not is_valid_email:
            flash(f'Correo inválido: {email_error}', 'danger')
            return render_template('forgot_password.html')

        user = User.query.filter_by(email=normalized_email).first()  # Busca al usuario
        flash('Si el correo está registrado, recibirás instrucciones de recuperación', 'info')  # Mensaje uniforme

        if user:
            old_tokens = PasswordResetToken.query.filter_by(user_id=user.id, used=False).all()  # Tokens previos
            for token in old_tokens:
                token.mark_as_used()  # Invalida tokens anteriores

            reset_token = PasswordResetToken(user_id=user.id, expiration_hours=1)  # Crea token nuevo
            db.session.add(reset_token)  # Agrega a la sesión
            db.session.commit()          # Guarda en la base

            email_sent = send_password_reset_email(user, reset_token.token, mail)  # Envía correo
            if not email_sent:
                db.session.delete(reset_token)  # Limpia el token si falló el envío
                db.session.commit()
                flash('Error al enviar el correo. Intenta más tarde.', 'danger')
                return render_template('forgot_password.html')

        return redirect(url_for('login'))  # Redirige a login tras procesar

    return render_template('forgot_password.html')  # Muestra formulario en GET



@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Propósito: permitir cambio de contraseña usando un token válido.
    Entradas: token en la URL; (POST form) password y confirm_password.
    Salidas: render de formulario o redirect a login tras éxito.
    Dependencias: PasswordResetToken.get_valid_token, bcrypt, db.session.
    """
    # Permitir cambio de contraseña usando un token válido
    if current_user.is_authenticated:
        return redirect(url_for('upload_files'))  # Evita uso si ya está logueado

    reset_token = PasswordResetToken.get_valid_token(token)  # Valida token
    if not reset_token:
        flash('Enlace inválido o expirado. Solicita uno nuevo.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')                # Nueva contraseña
        confirm_password = request.form.get('confirm_password')# Confirmación

        if not password or not confirm_password:
            flash('Todos los campos son requeridos', 'danger')
            return render_template('reset_password.html', token=token)

        if password != confirm_password:  # Coincidencia
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('reset_password.html', token=token)

        is_valid_password, password_error = validate_password_strength(password)  # Fortaleza
        if not is_valid_password:
            flash(password_error, 'danger')
            return render_template('reset_password.html', token=token)

        user = reset_token.user                                        # Usuario dueño del token
        user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')  # Re-hash
        reset_token.mark_as_used()                                     # Marca token como usado
        db.session.commit()                                            # Guarda cambios

        flash('Contraseña actualizada. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)  # Muestra formulario en GET


@app.route('/dashboard')
@suscripcion_requerida
def dashboard():
    """
    Propósito: listar usuarios (ajusta la política de acceso según tu criterio).
    Entradas: ninguna.
    Salidas: render de dashboard con usuarios.
    Dependencias: User.
    Nota: si ya no hay roles, aquí puedes permitir solo si la cuenta está ACTIVA o implementar tu propio check.
    """
    # Ejemplo simple: solo usuarios con cuenta activa pueden ver el dashboard
    if current_user.estado_cuenta != 'ACTIVA':
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('upload_files'))

    users = User.query.order_by(User.fecha_creacion.desc()).all()
    return render_template('dashboard.html', users=users)


@app.route('/download-desktop-app')
@suscripcion_requerida
def download_desktop_app():
    """Ruta para descargar la aplicación de escritorio"""
    try:
        # Ruta del ejecutable
        exe_path = os.path.join(os.path.dirname(__file__), 'downloads', 'FAT_Testing.exe')

        # Verificar que el archivo existe
        if not os.path.exists(exe_path):
            flash('La aplicación de escritorio no está disponible en este momento. Por favor contacta al administrador.', 'warning')
            return redirect(url_for('upload_files'))

        # Enviar archivo para descarga
        return send_file(
            exe_path,
            as_attachment=True,
            download_name='FAT_Testing.exe',
            mimetype='application/octet-stream'
        )
    except Exception as e:
        flash(f'Error al descargar la aplicación: {str(e)}', 'danger')
        return redirect(url_for('upload_files'))


# ====== RUTAS DE LA APLICACIÓN ======

@app.route('/app', methods=['GET', 'POST'])
@suscripcion_requerida
def upload_files():

    opciones = [
        'SW L2 9200',
        'SW L2 9300',
        'SW L2 9500',
    ]

    if request.method == 'POST':

        
        file_type = request.form.get('fileType')
        file = request.files.get('file')
        processed_files = []
        img_1 = request.files.getlist('imageFiles1')
        img_2 = request.files.getlist('imageFiles2')
        img_3 = request.files.getlist('imageFiles3')
        proyecto = request.form.get('proyecto')
        cliente = request.form.get('cliente')
        ordenCompra = request.form.get('ordenCompra')
        notaVenta = request.form.get('notaVenta')     
        
        if file:
            filename = secure_filename(file.filename)
            # Plantilla basada en el tipo de archivo
            if file_type == "SW L2 9200" or file_type == "SW L2 9300":
                docx_template_path = os.path.join('plantillas', 'Template Extraccion SW 9200 - 9300.docx')
                    
            elif file_type == "SW L2 9500":
                docx_template_path = os.path.join('plantillas', 'Template Extraccion SW 9500.docx')

            elif file_type == "SW L3 9348GC" or file_type == "SW L3 C93180YC":
                docx_template_path = os.path.join('plantillas', 'Template Extraccion SW 9348GC - C93180YC.docx')
                    
            elif file_type == "SW IE3300" or file_type == "SW IE4010":
                docx_template_path = os.path.join('plantillas', 'Template Extraccion SW IE 3300 - 4010.docx')
                    
            elif file_type == "Router C8500":
                docx_template_path = os.path.join('plantillas', 'Template Extraccion Router C8500.docx')
                    
            elif file_type == "Router ISR4431":
                docx_template_path = os.path.join('plantillas', 'Template Extraccion Router ISR4431.docx')

            elif file_type == "AP C9115AXI" or file_type == "AP C9120AXE" or file_type == "AP C9130AXI":
                docx_template_path = os.path.join('plantillas', 'Template Extraccion C9115AXI-A,C9120AXE-A,C9130AXI-A.docx')

            elif file_type == "Check Point 6200" or file_type == "Check Point 6600" :
                docx_template_path = os.path.join('plantillas', 'Template Extraccion Check Point 6200P - 6600P.docx')
                    

            # Procesamiento de archivo
                    
            word_buffer, download_filename = procesar_archivo(
                file.stream, 
                docx_template_path, 
                img_1,
                img_2,
                img_3,
                proyecto,
                cliente,
                ordenCompra,
                notaVenta,
                file_type
                )
            
            # Limpiar el nombre del archivo
            download_filename = download_filename.strip().replace('\n', '').replace('\r', '')
            download_filename = secure_filename(download_filename)
            
        return send_file(word_buffer, as_attachment=True, download_name=download_filename, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    
    return render_template('informes.html', opciones=opciones)

# ====== COMANDOS CLI ======

@app.cli.command()
def init_db():
    """Inicializar la base de datos"""
    with app.app_context():
        db.create_all()
        print('Base de datos inicializada!')


@app.cli.command()
def create_admin():
    """
    Propósito: crear un usuario desde la línea de comandos (sin roles).
    Entradas: prompts de consola para email, password, nombre, apellido.
    Salidas: imprime resultado en consola.
    Dependencias: User, db.session, bcrypt (dentro del constructor).
    """
    # Crear un usuario desde la línea de comandos (sin roles)
    with app.app_context():
        email = input('Email: ').strip()         # Pide email
        password = input('Contraseña: ')         # Pide contraseña
        nombre = input('Nombre: ').strip()       # Pide nombre
        apellido = input('Apellido: ').strip()   # Pide apellido

        if User.query.filter_by(email=email).first():  # Revisa si ya existe
            print('El correo ya existe')
            return

        user = User(email=email, password=password, nombre=nombre, apellido=apellido)  # Crea usuario
        db.session.add(user)  # Agrega a la sesión
        db.session.commit()   # Guarda en la base
        print(f'Usuario {email} creado exitosamente')



# Iniciar la aplicación
if __name__ == '__main__':
    # Crear las tablas si no existen
    with app.app_context():
        db.create_all()

    #app.run(host="0.0.0.0", port=80, debug=True, ssl_context="adhoc")
    app.run(host="0.0.0.0", port=80, debug=True)