# Fat testing app 1.0v

Este proyecto es una aplicación Flask diseñada para procesar archivos de texto cargados por el usuario, extraer información relevante y generar documentos personalizados en formato Word (.docx). 
La aplicación permite manejar varios tipos de dispositivos y formatos de archivo, destacando palabras clave y estructurando la información de manera organizada en plantillas específicas.


# Funcionalidades principales:

1. Carga de archivos múltiple:
Permite a los usuarios cargar múltiples archivos simultáneamente a través de una interfaz web.

2. Procesamiento de texto:
Extrae información específica de los archivos cargados, según el tipo de dispositivo (SW9200, SW9300, SW9500, AP, Nexus, etc.).
Resalta palabras clave configurables en el texto procesado.
Genera documentos personalizados en formato Word con la información procesada, utilizando plantillas predefinidas.

3. Compatibilidad con dispositivos:
Diseñado para manejar información de diversos dispositivos, como switches Cisco Catalyst (SW9200, SW9300, SW9500), puntos de acceso (AP), y switches Nexus.
Lógica de procesamiento específica para cada tipo de dispositivo.

4. Generación de documentos Word:
Utiliza plantillas de Word para insertar la información procesada.
Aplica estilos personalizados, como el uso de la fuente Cascadia Code, tamaño de fuente configurable y resaltado de palabras clave.

5. Descarga de documentos:
Genera un archivo ZIP que contiene todos los documentos procesados, disponible para descargar al usuario.

# Registro de resultados temporales:
Los documentos procesados se guardan temporalmente en un directorio designado y se eliminan una vez incluidos en el archivo ZIP final.

# Requisitos:
Python 3.7 o superior.
Librerías necesarias (instalables con pip install <nombre_librería>):
Flask - Para crear la aplicación web.
python-docx - Para generar y modificar documentos Word.
werkzeug - Para manejar de forma segura los nombres de archivo cargados.
uuid - Para generar nombres únicos para archivos temporales.
re - Para procesar expresiones regulares.
zipfile - Para generar archivos ZIP descargables.



