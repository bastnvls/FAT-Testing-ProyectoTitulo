from flask import Flask, request, render_template, send_file, redirect, url_for, flash
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
from flask_login import LoginManager, login_required, current_user
from models import db, bcrypt, User
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar extensiones
db.init_app(app)
bcrypt.init_app(app)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def aplicar_fuente_cascadia_code(run, size_pt):
    run.font.name = 'Cascadia Code'
    run.font.size = Pt(size_pt)
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Cascadia Code')

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
            
            # Crear run con el texto nuevo
            run = p.add_run(str(text))
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
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if marker in cell.text:
                    cell.text = ''
                    para = cell.add_paragraph()
                    para.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                    for line in texto.split('\n'):
                        run = para.add_run(line)
                        aplicar_fuente_cascadia_code(run, size_pt)
                        para.add_run('\n')  # salto tras cada línea
                    paras.append(para)
    return paras

def insertar_info_dispositivo(doc, modelo, serial, version):

    # También revisamos las celdas de todas las tablas en el documento, por si no están en párrafos
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if "{{modelo}}" in cell.text:
                    cell.text = cell.text.replace("{{modelo}}", modelo if modelo else "")
                    para = cell.paragraphs[0]
                    para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER  # Centrar texto
                    # Aplicar formato Arial 11 a todo el párrafo
                    for run in para.runs:
                        run.font.name = 'Arial'
                        run.font.size = Pt(11)
                        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')

                if "{{serial}}" in cell.text:
                    cell.text = cell.text.replace("{{serial}}", serial if serial else "")
                    para = cell.paragraphs[0]
                    para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER  # Centrar texto
                    for run in para.runs:
                        run.font.name = 'Arial'
                        run.font.size = Pt(11)
                        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')

                if "{{version}}" in cell.text:
                    cell.text = cell.text.replace("{{version}}", version if version else "")
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


# ====== RUTAS DE AUTENTICACIÓN ======

@app.route('/')
def landing():
    """Landing page con información del proyecto"""
    if current_user.is_authenticated:
        return redirect(url_for('upload_files'))
    return render_template('landing.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Ruta para registro de nuevos usuarios"""
    if current_user.is_authenticated:
        return redirect(url_for('upload_files'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validaciones
        if not username or not email or not password:
            flash('Todos los campos son requeridos', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'danger')
            return render_template('register.html')

        # Verificar si el usuario ya existe
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya está en uso', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('El correo electrónico ya está registrado', 'danger')
            return render_template('register.html')

        # Crear nuevo usuario
        new_user = User(username=username, email=email, password=password, role='user')
        db.session.add(new_user)
        db.session.commit()

        flash('Registro exitoso! Por favor inicia sesión', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Ruta para inicio de sesión"""
    if current_user.is_authenticated:
        return redirect(url_for('upload_files'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        if not email or not password:
            flash('Por favor ingresa tu correo y contraseña', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            from flask_login import login_user
            login_user(user, remember=remember)
            flash(f'Bienvenido, {user.username}!', 'success')

            # Redirigir a la página solicitada o a la app
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('upload_files'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Ruta para cerrar sesión"""
    from flask_login import logout_user
    logout_user()
    flash('Has cerrado sesión exitosamente', 'info')
    return redirect(url_for('landing'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard para administradores"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('upload_files'))

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('dashboard.html', users=users)


# ====== RUTAS DE LA APLICACIÓN ======

@app.route('/app', methods=['GET', 'POST'])
@login_required
def upload_files():

    opciones = [
        'AP C9115AXI',
        'AP C9120AXE',
        'AP C9130AXI',
        'SW L2 9200',
        'SW L2 9300',
        'SW L2 9500',
        'SW L3 9348GC',
        'SW L3 C93180YC',
        'SW IE3300',
        'SW IE4010',
        'Check Point 6200',
        'Check Point 6600',
        'Router ISR4431',
        'Router C8500',
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

    
    return render_template('index.html', opciones=opciones)

# ====== COMANDOS CLI ======

@app.cli.command()
def init_db():
    """Inicializar la base de datos"""
    with app.app_context():
        db.create_all()
        print('Base de datos inicializada!')


@app.cli.command()
def create_admin():
    """Crear usuario administrador"""
    with app.app_context():
        username = input('Nombre de usuario: ')
        email = input('Email: ')
        password = input('Contraseña: ')

        if User.query.filter_by(username=username).first():
            print('El usuario ya existe!')
            return

        admin = User(username=username, email=email, password=password, role='admin')
        db.session.add(admin)
        db.session.commit()
        print(f'Usuario administrador {username} creado exitosamente!')


# Iniciar la aplicación
if __name__ == '__main__':
    # Crear las tablas si no existen
    with app.app_context():
        db.create_all()

    #app.run(host="0.0.0.0", port=80, debug=True, ssl_context="adhoc")
    app.run(host="0.0.0.0", port=80, debug=True)