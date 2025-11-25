#!/usr/bin/env python3
"""
Script para pruebas de diagnóstico en switches Cisco Catalyst 9200
Conexión via cable consola usando pyserial

Uso:
    1. Instalar pyserial: pip install pyserial
    2. Ajustar PUERTO_SERIAL según tu sistema
    3. Ejecutar: python cisco_9200_test.py
"""

import serial
import time
import re
from datetime import datetime


# =============================================================================
# CONFIGURACIÓN GENERAL - AJUSTAR SEGÚN TU ENTORNO
# =============================================================================

# Puerto serial (ajustar según tu sistema operativo)
# Windows: "COM3", "COM4", etc.
# Linux: "/dev/ttyUSB0", "/dev/ttyS0", etc.
# Mac: "/dev/tty.usbserial-XXXX"
PUERTO_SERIAL = "/dev/ttyUSB0"

# Configuración estándar para consola Cisco
BAUDRATE = 9600
BYTESIZE = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOPBITS = serial.STOPBITS_ONE
TIMEOUT_LECTURA = 2  # segundos

# Credenciales (ajustar según tu dispositivo)
PASSWORD_ENABLE = "cisco"  # Contraseña para modo privilegiado

# Archivo de salida
ARCHIVO_SALIDA = "resultado_pruebas_cisco_9200.txt"

# Tiempos de espera (segundos)
ESPERA_COMANDO = 1
ESPERA_RELOAD = 180  # 3 minutos para el reload


# =============================================================================
# FUNCIONES DE CONEXIÓN SERIAL
# =============================================================================

def abrir_conexion_serial(puerto, baudrate):
    """
    Abre una conexión serial con el dispositivo Cisco.
    
    Args:
        puerto: Puerto serial (ej: COM3, /dev/ttyUSB0)
        baudrate: Velocidad de transmisión (normalmente 9600)
    
    Returns:
        Objeto serial si la conexión es exitosa, None si falla
    """
    try:
        conexion = serial.Serial(
            port=puerto,
            baudrate=baudrate,
            bytesize=BYTESIZE,
            parity=PARITY,
            stopbits=STOPBITS,
            timeout=TIMEOUT_LECTURA,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        print(f"[OK] Conexión establecida en {puerto} a {baudrate} baudios")
        return conexion
    
    except serial.SerialException as error:
        print(f"[ERROR] No se pudo abrir el puerto {puerto}: {error}")
        return None


def cerrar_conexion_serial(conexion):
    """
    Cierra la conexión serial de forma segura.
    
    Args:
        conexion: Objeto serial a cerrar
    """
    if conexion and conexion.is_open:
        conexion.close()
        print("[OK] Conexión serial cerrada")


# =============================================================================
# FUNCIONES DE COMUNICACIÓN CON EL DISPOSITIVO
# =============================================================================

def leer_respuesta_completa(conexion, timeout_total=10):
    """
    Lee la respuesta completa del dispositivo hasta que no haya más datos.
    
    Args:
        conexion: Objeto serial activo
        timeout_total: Tiempo máximo de espera total (segundos)
    
    Returns:
        String con toda la respuesta recibida
    """
    respuesta_completa = ""
    tiempo_inicio = time.time()
    
    while True:
        # Verificar timeout total
        if time.time() - tiempo_inicio > timeout_total:
            break
        
        # Leer bytes disponibles
        if conexion.in_waiting > 0:
            datos = conexion.read(conexion.in_waiting)
            try:
                respuesta_completa += datos.decode('ascii', errors='ignore')
            except:
                respuesta_completa += datos.decode('latin-1', errors='ignore')
            tiempo_inicio = time.time()  # Resetear timeout si recibimos datos
        else:
            # Si no hay datos, esperar un poco
            time.sleep(0.1)
            
            # Si después de esperar sigue sin datos, verificar si terminó
            if conexion.in_waiting == 0:
                time.sleep(0.5)
                if conexion.in_waiting == 0:
                    break
    
    return respuesta_completa


def enviar_comando(conexion, comando, espera=ESPERA_COMANDO):
    """
    Envía un comando al dispositivo y espera la respuesta.
    
    Args:
        conexion: Objeto serial activo
        comando: Comando a enviar (string)
        espera: Tiempo de espera después del comando (segundos)
    
    Returns:
        String con la respuesta del dispositivo
    """
    # Limpiar buffer de entrada antes de enviar
    conexion.reset_input_buffer()
    
    # Enviar comando con retorno de carro
    comando_bytes = (comando + "\n").encode('ascii')
    conexion.write(comando_bytes)
    
    print(f"[ENVIADO] {comando}")
    
    # Esperar a que el dispositivo procese el comando
    time.sleep(espera)
    
    # Leer toda la respuesta disponible
    respuesta = leer_respuesta_completa(conexion)
    
    return respuesta


def manejar_more_prompt(conexion, respuesta):
    """
    Maneja el prompt '--More--' que aparece en salidas largas de Cisco.
    Envía espacio para continuar hasta obtener toda la salida.
    
    Args:
        conexion: Objeto serial activo
        respuesta: Respuesta inicial del comando
    
    Returns:
        String con la respuesta completa (sin --More--)
    """
    respuesta_total = respuesta
    
    while "--More--" in respuesta_total:
        # Enviar espacio para continuar
        conexion.write(b" ")
        time.sleep(0.5)
        
        # Leer más datos
        nueva_respuesta = leer_respuesta_completa(conexion, timeout_total=5)
        
        # Limpiar el --More-- de la respuesta anterior
        respuesta_total = respuesta_total.replace("--More--", "")
        respuesta_total += nueva_respuesta
    
    return respuesta_total


def ejecutar_comando_completo(conexion, comando, espera=ESPERA_COMANDO):
    """
    Ejecuta un comando y maneja automáticamente el paginado --More--.
    
    Args:
        conexion: Objeto serial activo
        comando: Comando a ejecutar
        espera: Tiempo de espera después del comando
    
    Returns:
        String con la respuesta completa del comando
    """
    respuesta = enviar_comando(conexion, comando, espera)
    respuesta = manejar_more_prompt(conexion, respuesta)
    return respuesta


# =============================================================================
# FUNCIONES DE AUTENTICACIÓN Y PREPARACIÓN
# =============================================================================

def despertar_consola(conexion):
    """
    'Despierta' la consola enviando Enter para obtener el prompt.
    
    Args:
        conexion: Objeto serial activo
    
    Returns:
        String con la respuesta (debería mostrar el prompt)
    """
    print("[INFO] Despertando consola...")
    
    # Enviar varios Enter para activar la consola
    for _ in range(3):
        conexion.write(b"\r\n")
        time.sleep(0.5)
    
    respuesta = leer_respuesta_completa(conexion, timeout_total=5)
    return respuesta


def entrar_modo_enable(conexion, password):
    """
    Entra al modo privilegiado (enable) del dispositivo.
    
    Args:
        conexion: Objeto serial activo
        password: Contraseña para modo enable
    
    Returns:
        True si entró correctamente, False si falló
    """
    print("[INFO] Entrando a modo privilegiado (enable)...")
    
    # Enviar comando enable
    respuesta = enviar_comando(conexion, "enable", espera=1)
    
    # Si pide password, enviarlo
    if "Password:" in respuesta or "password:" in respuesta.lower():
        respuesta = enviar_comando(conexion, password, espera=1)
    
    # Verificar si estamos en modo enable (prompt termina en #)
    if "#" in respuesta:
        print("[OK] Modo privilegiado activado")
        return True
    else:
        print("[ADVERTENCIA] Puede que ya estemos en modo enable o hubo un error")
        return True  # Continuar de todas formas


def configurar_terminal(conexion):
    """
    Configura el terminal para evitar paginación y mejorar la salida.
    
    Args:
        conexion: Objeto serial activo
    """
    print("[INFO] Configurando terminal...")
    
    # Desactivar paginación (terminal length 0)
    ejecutar_comando_completo(conexion, "terminal length 0")
    
    # Desactivar ancho de terminal para evitar cortes
    ejecutar_comando_completo(conexion, "terminal width 512")
    
    print("[OK] Terminal configurado")


# =============================================================================
# FUNCIONES DE ANÁLISIS DE SALIDAS
# =============================================================================

def contar_fuentes_poder(salida_show_inventory):
    """
    Cuenta el número de fuentes de poder según 'show inventory'.
    
    Args:
        salida_show_inventory: Salida del comando show inventory
    
    Returns:
        Número de fuentes de poder encontradas
    """
    # Buscar patrones comunes de PSU en Cisco
    patron_psu = re.compile(r'(PWR-|Power Supply|PSU)', re.IGNORECASE)
    
    coincidencias = patron_psu.findall(salida_show_inventory)
    cantidad = len(coincidencias)
    
    # Mínimo 1 fuente si no se detectan
    if cantidad == 0:
        print("[INFO] No se detectaron fuentes de poder, asumiendo 1")
        cantidad = 1
    
    print(f"[INFO] Fuentes de poder detectadas: {cantidad}")
    return cantidad


def contar_ventiladores(salida_show_inventory):
    """
    Cuenta el número de ventiladores según 'show inventory'.
    
    Args:
        salida_show_inventory: Salida del comando show inventory
    
    Returns:
        Número de ventiladores encontrados
    """
    # Buscar patrones comunes de FAN en Cisco
    patron_fan = re.compile(r'(FAN|Fan Tray)', re.IGNORECASE)
    
    coincidencias = patron_fan.findall(salida_show_inventory)
    cantidad = len(coincidencias)
    
    # Mínimo 1 ventilador si no se detectan
    if cantidad == 0:
        print("[INFO] No se detectaron ventiladores, asumiendo 1")
        cantidad = 1
    
    print(f"[INFO] Ventiladores detectados: {cantidad}")
    return cantidad


# =============================================================================
# FUNCIONES DE ARCHIVO DE SALIDA
# =============================================================================

def iniciar_archivo_salida(archivo):
    """
    Crea el archivo de salida con el encabezado inicial.
    
    Args:
        archivo: Nombre del archivo a crear
    
    Returns:
        True si se creó correctamente, False si falló
    """
    try:
        with open(archivo, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RESULTADO DE PRUEBAS - CISCO CATALYST 9200\n")
            f.write("=" * 80 + "\n")
            f.write(f"Fecha y hora de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
        print(f"[OK] Archivo de salida creado: {archivo}")
        return True
    
    except IOError as error:
        print(f"[ERROR] No se pudo crear el archivo: {error}")
        return False


def escribir_en_archivo(archivo, texto):
    """
    Agrega texto al archivo de salida.
    
    Args:
        archivo: Nombre del archivo
        texto: Texto a agregar
    """
    try:
        with open(archivo, 'a', encoding='utf-8') as f:
            f.write(texto)
    except IOError as error:
        print(f"[ERROR] No se pudo escribir en el archivo: {error}")


def escribir_inicio_prueba(archivo, numero_prueba, descripcion):
    """
    Escribe el marcador de inicio de una prueba.
    
    Args:
        archivo: Nombre del archivo
        numero_prueba: Número de la prueba
        descripcion: Descripción breve de la prueba
    """
    texto = f"\n{'#' * 80}\n"
    texto += f"### INICIO PRUEBA {numero_prueba}: {descripcion}\n"
    texto += f"### Hora: {datetime.now().strftime('%H:%M:%S')}\n"
    texto += f"{'#' * 80}\n\n"
    escribir_en_archivo(archivo, texto)
    print(f"\n[PRUEBA {numero_prueba}] INICIANDO: {descripcion}")


def escribir_fin_prueba(archivo, numero_prueba):
    """
    Escribe el marcador de fin de una prueba.
    
    Args:
        archivo: Nombre del archivo
        numero_prueba: Número de la prueba
    """
    texto = f"\n{'#' * 80}\n"
    texto += f"### FIN PRUEBA {numero_prueba}\n"
    texto += f"### Hora: {datetime.now().strftime('%H:%M:%S')}\n"
    texto += f"{'#' * 80}\n\n"
    escribir_en_archivo(archivo, texto)
    print(f"[PRUEBA {numero_prueba}] FINALIZADA")


def escribir_comando_resultado(archivo, comando, resultado):
    """
    Escribe un comando y su resultado en el archivo.
    
    Args:
        archivo: Nombre del archivo
        comando: Comando ejecutado
        resultado: Salida del comando
    """
    texto = f"\n--- Comando: {comando} ---\n"
    texto += resultado
    texto += f"\n--- Fin comando: {comando} ---\n"
    escribir_en_archivo(archivo, texto)


def finalizar_archivo_salida(archivo):
    """
    Agrega el pie de página al archivo de salida.
    
    Args:
        archivo: Nombre del archivo
    """
    texto = "\n" + "=" * 80 + "\n"
    texto += f"PRUEBAS FINALIZADAS: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    texto += "=" * 80 + "\n"
    escribir_en_archivo(archivo, texto)
    print(f"\n[OK] Resultados guardados en: {archivo}")


# =============================================================================
# FUNCIONES DE PRUEBAS
# =============================================================================

def ejecutar_prueba_1(conexion, archivo):
    """
    Prueba 1: show version, show inventory
    
    Args:
        conexion: Objeto serial activo
        archivo: Archivo de salida
    
    Returns:
        Salida del show inventory (para análisis posterior)
    """
    escribir_inicio_prueba(archivo, 1, "show version, show inventory")
    
    # Ejecutar show version
    resultado_version = ejecutar_comando_completo(conexion, "show version", espera=2)
    escribir_comando_resultado(archivo, "show version", resultado_version)
    
    # Ejecutar show inventory
    resultado_inventory = ejecutar_comando_completo(conexion, "show inventory", espera=2)
    escribir_comando_resultado(archivo, "show inventory", resultado_inventory)
    
    escribir_fin_prueba(archivo, 1)
    
    return resultado_inventory


def ejecutar_prueba_2(conexion, archivo, cantidad_psu):
    """
    Prueba 2: show environment power (repetido por cada fuente de poder)
    
    Args:
        conexion: Objeto serial activo
        archivo: Archivo de salida
        cantidad_psu: Número de fuentes de poder a consultar
    """
    escribir_inicio_prueba(archivo, 2, f"show environment power ({cantidad_psu} fuente(s))")
    
    for i in range(cantidad_psu):
        comentario = f"Consulta {i + 1} de {cantidad_psu}"
        escribir_en_archivo(archivo, f"\n=== {comentario} ===\n")
        
        resultado = ejecutar_comando_completo(conexion, "show environment power", espera=2)
        escribir_comando_resultado(archivo, f"show environment power (#{i + 1})", resultado)
        
        # Pequeña pausa entre consultas
        time.sleep(0.5)
    
    escribir_fin_prueba(archivo, 2)


def ejecutar_prueba_3(conexion, archivo, cantidad_fan):
    """
    Prueba 3: show environment fan (repetido por cada ventilador)
    
    Args:
        conexion: Objeto serial activo
        archivo: Archivo de salida
        cantidad_fan: Número de ventiladores a consultar
    """
    escribir_inicio_prueba(archivo, 3, f"show environment fan ({cantidad_fan} ventilador(es))")
    
    for i in range(cantidad_fan):
        comentario = f"Consulta {i + 1} de {cantidad_fan}"
        escribir_en_archivo(archivo, f"\n=== {comentario} ===\n")
        
        resultado = ejecutar_comando_completo(conexion, "show environment fan", espera=2)
        escribir_comando_resultado(archivo, f"show environment fan (#{i + 1})", resultado)
        
        # Pequeña pausa entre consultas
        time.sleep(0.5)
    
    escribir_fin_prueba(archivo, 3)


def ejecutar_prueba_4(conexion, archivo, password_enable):
    """
    Prueba 4: reload, show version, enable
    
    ADVERTENCIA: Esta prueba reinicia el equipo.
    
    Args:
        conexion: Objeto serial activo
        archivo: Archivo de salida
        password_enable: Contraseña para modo enable
    """
    escribir_inicio_prueba(archivo, 4, "reload, show version, enable")
    
    escribir_en_archivo(archivo, "\n=== INICIANDO RELOAD DEL EQUIPO ===\n")
    escribir_en_archivo(archivo, f"Hora de inicio reload: {datetime.now().strftime('%H:%M:%S')}\n")
    
    # Enviar comando reload
    conexion.write(b"reload\n")
    time.sleep(1)
    
    # Leer respuesta (puede pedir confirmación)
    respuesta = leer_respuesta_completa(conexion, timeout_total=5)
    escribir_en_archivo(archivo, f"Respuesta inicial: {respuesta}\n")
    
    # Manejar: "System configuration has been modified. Save? [yes/no]:"
    if "Save?" in respuesta or "save" in respuesta.lower():
        conexion.write(b"no\n")  # No guardar cambios
        time.sleep(1)
        respuesta = leer_respuesta_completa(conexion, timeout_total=5)
        escribir_en_archivo(archivo, f"Respuesta a Save: {respuesta}\n")
    
    # Manejar: "Proceed with reload? [confirm]"
    if "confirm" in respuesta.lower() or "proceed" in respuesta.lower():
        conexion.write(b"\n")  # Confirmar reload
        time.sleep(1)
        respuesta = leer_respuesta_completa(conexion, timeout_total=5)
        escribir_en_archivo(archivo, f"Confirmación enviada: {respuesta}\n")
    
    # Esperar a que el equipo reinicie
    print(f"[INFO] Esperando {ESPERA_RELOAD} segundos para que el equipo reinicie...")
    escribir_en_archivo(archivo, f"\nEsperando {ESPERA_RELOAD} segundos para reinicio...\n")
    
    tiempo_inicio_reload = time.time()
    
    # Monitorear el proceso de arranque
    while time.time() - tiempo_inicio_reload < ESPERA_RELOAD:
        if conexion.in_waiting > 0:
            datos = leer_respuesta_completa(conexion, timeout_total=2)
            if datos:
                escribir_en_archivo(archivo, datos)
                print(".", end="", flush=True)
        time.sleep(5)
    
    print()  # Nueva línea después de los puntos
    
    # Intentar despertar la consola después del reload
    escribir_en_archivo(archivo, "\n=== EQUIPO REINICIADO, RECONECTANDO ===\n")
    
    for intento in range(10):
        despertar_consola(conexion)
        time.sleep(2)
        
        respuesta = leer_respuesta_completa(conexion, timeout_total=3)
        escribir_en_archivo(archivo, f"Intento {intento + 1}: {respuesta}\n")
        
        # Verificar si tenemos prompt
        if ">" in respuesta or "#" in respuesta:
            print(f"[OK] Consola disponible después de {intento + 1} intentos")
            break
        
        time.sleep(3)
    
    # Ejecutar show version después del reload
    resultado_version = ejecutar_comando_completo(conexion, "show version", espera=2)
    escribir_comando_resultado(archivo, "show version (post-reload)", resultado_version)
    
    # Entrar a modo enable
    escribir_en_archivo(archivo, "\n=== ENTRANDO A MODO ENABLE ===\n")
    entrar_modo_enable(conexion, password_enable)
    
    # Verificar que estamos en modo enable
    respuesta_enable = ejecutar_comando_completo(conexion, "", espera=1)
    escribir_en_archivo(archivo, f"Prompt actual: {respuesta_enable}\n")
    
    escribir_fin_prueba(archivo, 4)


def ejecutar_prueba_5(conexion, archivo):
    """
    Prueba 5: show inventory all, show interface ethernet
    
    Nota: "show interface ethernet" no es sintaxis válida en Cisco IOS-XE.
    Se ejecuta "show interfaces" y "show interfaces status" como alternativas.
    
    Args:
        conexion: Objeto serial activo
        archivo: Archivo de salida
    """
    escribir_inicio_prueba(archivo, 5, "show inventory all, show interfaces")
    
    # Ejecutar show inventory all
    resultado_inventory = ejecutar_comando_completo(conexion, "show inventory all", espera=3)
    escribir_comando_resultado(archivo, "show inventory all", resultado_inventory)
    
    # Ejecutar show interfaces (todas las interfaces)
    resultado_interfaces = ejecutar_comando_completo(conexion, "show interfaces", espera=5)
    escribir_comando_resultado(archivo, "show interfaces", resultado_interfaces)
    
    # Mostrar estado resumido de interfaces
    resultado_status = ejecutar_comando_completo(conexion, "show interfaces status", espera=2)
    escribir_comando_resultado(archivo, "show interfaces status", resultado_status)
    
    escribir_fin_prueba(archivo, 5)


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    """
    Función principal que ejecuta todas las pruebas en secuencia.
    """
    print("\n" + "=" * 60)
    print("SCRIPT DE PRUEBAS - CISCO CATALYST 9200")
    print("=" * 60 + "\n")
    
    # Mostrar configuración actual
    print(f"Puerto serial: {PUERTO_SERIAL}")
    print(f"Baudrate: {BAUDRATE}")
    print(f"Archivo de salida: {ARCHIVO_SALIDA}")
    print()
    
    # Inicializar archivo de salida
    if not iniciar_archivo_salida(ARCHIVO_SALIDA):
        print("[ERROR] No se pudo inicializar el archivo de salida. Abortando.")
        return
    
    # Abrir conexión serial
    conexion = abrir_conexion_serial(PUERTO_SERIAL, BAUDRATE)
    if not conexion:
        print("[ERROR] No se pudo establecer conexión serial. Abortando.")
        return
    
    try:
        # Preparar la conexión
        despertar_consola(conexion)
        entrar_modo_enable(conexion, PASSWORD_ENABLE)
        configurar_terminal(conexion)
        
        # =====================================================================
        # PRUEBA 1: show version, show inventory
        # =====================================================================
        resultado_inventory = ejecutar_prueba_1(conexion, ARCHIVO_SALIDA)
        
        # Analizar inventory para determinar cantidad de PSU y FAN
        cantidad_psu = contar_fuentes_poder(resultado_inventory)
        cantidad_fan = contar_ventiladores(resultado_inventory)
        
        # =====================================================================
        # PRUEBA 2: show environment power
        # =====================================================================
        ejecutar_prueba_2(conexion, ARCHIVO_SALIDA, cantidad_psu)
        
        # =====================================================================
        # PRUEBA 3: show environment fan
        # =====================================================================
        ejecutar_prueba_3(conexion, ARCHIVO_SALIDA, cantidad_fan)
        
        # =====================================================================
        # PRUEBA 4: reload, show version, enable
        # =====================================================================
        # ADVERTENCIA: Esta prueba reinicia el equipo
        # Para activarla, cambiar EJECUTAR_RELOAD a True
        
        EJECUTAR_RELOAD = False  # Cambiar a True para ejecutar el reload
        
        if EJECUTAR_RELOAD:
            print("\n" + "!" * 60)
            print("EJECUTANDO RELOAD - EL EQUIPO SE REINICIARÁ")
            print("!" * 60 + "\n")
            ejecutar_prueba_4(conexion, ARCHIVO_SALIDA, PASSWORD_ENABLE)
        else:
            print("\n" + "!" * 60)
            print("ADVERTENCIA: Prueba 4 (reload) OMITIDA por seguridad.")
            print("Para ejecutarla, cambiar EJECUTAR_RELOAD = True en el código.")
            print("!" * 60 + "\n")
            
            escribir_inicio_prueba(ARCHIVO_SALIDA, 4, "reload [OMITIDO POR SEGURIDAD]")
            escribir_en_archivo(ARCHIVO_SALIDA, 
                "\n*** RELOAD NO EJECUTADO ***\n"
                "Para ejecutar el reload, cambiar EJECUTAR_RELOAD = True\n")
            escribir_fin_prueba(ARCHIVO_SALIDA, 4)
        
        # =====================================================================
        # PRUEBA 5: show inventory all, show interfaces
        # =====================================================================
        ejecutar_prueba_5(conexion, ARCHIVO_SALIDA)
        
        # Finalizar archivo
        finalizar_archivo_salida(ARCHIVO_SALIDA)
        
        print("\n" + "=" * 60)
        print("TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 60 + "\n")
        
    except KeyboardInterrupt:
        print("\n[INTERRUPCIÓN] Pruebas canceladas por el usuario.")
        escribir_en_archivo(ARCHIVO_SALIDA, "\n*** PRUEBAS CANCELADAS POR EL USUARIO ***\n")
        
    except Exception as error:
        print(f"\n[ERROR CRÍTICO] {error}")
        escribir_en_archivo(ARCHIVO_SALIDA, f"\n*** ERROR CRÍTICO: {error} ***\n")
        
    finally:
        # Siempre cerrar la conexión
        cerrar_conexion_serial(conexion)


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    main()