import sys
import os
from datetime import datetime
from typing import Optional, Tuple, List
import logging
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QMessageBox, QFrame, QTextEdit,
                               QSpinBox, QCheckBox, QScrollArea, QGroupBox, QComboBox, QFileDialog)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor

# Importar módulos para conexión serial
import serial
from serial import SerialException, SerialTimeoutException
import time
import re

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos del proyecto
from models import db, User
from config import Config
from flask import Flask

# Configurar Flask para acceso a BD
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# =============================================================================
# CONFIGURACIÓN DE LOGGING
# =============================================================================
logging.basicConfig(
    level=logging.DEBUG,  # Cambiado a DEBUG para ver verificaciones detalladas
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fat_testing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES DE VALIDACIÓN Y CONFIGURACIÓN
# =============================================================================
# Puertos seriales válidos
VALID_PORT_PATTERN = re.compile(r'^(COM[1-9]\d?|/dev/tty(USB|ACM)\d+)$', re.IGNORECASE)

# Baudrates permitidos para dispositivos Cisco
VALID_BAUDRATES = [9600, 19200, 38400, 57600, 115200]

# Timeouts configurables
TIMEOUT_CONEXION_INICIAL = 5  # segundos para validar conexión inicial
TIMEOUT_LECTURA = 2  # segundos por defecto para leer respuesta
TIMEOUT_COMANDO = 10  # segundos para comandos normales
TIMEOUT_RELOAD = 180  # 3 minutos para reload

# Reintentos
MAX_REINTENTOS = 3
ESPERA_ENTRE_REINTENTOS = 2  # segundos

# Caracteres que indican prompt de Cisco
CISCO_PROMPTS = ['>', '#']

# Palabras clave que indican dispositivo Cisco válido
CISCO_KEYWORDS = ['Cisco', 'IOS', 'Catalyst', 'Switch', 'Router']

# =============================================================================
# EXCEPCIONES PERSONALIZADAS
# =============================================================================
class ConexionSerialError(Exception):
    """Excepción base para errores de conexión serial"""
    pass

class DispositivoNoDetectadoError(ConexionSerialError):
    """Se abrió el puerto pero no hay dispositivo Cisco respondiendo"""
    pass

class DispositivoDesconectadoError(ConexionSerialError):
    """El dispositivo se desconectó durante la ejecución"""
    pass

class TimeoutConexionError(ConexionSerialError):
    """Timeout esperando respuesta del dispositivo"""
    pass

class RespuestaInvalidaError(ConexionSerialError):
    """La respuesta del dispositivo no es válida"""
    pass

# =============================================================================
# FUNCIONES DE VALIDACIÓN
# =============================================================================
def validar_puerto_serial(puerto: str) -> bool:
    """Valida que el puerto serial tenga un formato válido"""
    if not puerto:
        return False
    return VALID_PORT_PATTERN.match(puerto) is not None

def validar_baudrate(baudrate: int) -> bool:
    """Valida que el baudrate sea uno de los valores permitidos"""
    return baudrate in VALID_BAUDRATES

def sanitizar_nombre_archivo(nombre: str) -> str:
    """Sanitiza nombre de archivo removiendo caracteres inválidos"""
    # Remover caracteres peligrosos
    nombre_limpio = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', nombre)
    # Remover .. para evitar path traversal
    nombre_limpio = nombre_limpio.replace('..', '_')
    # Limitar longitud
    return nombre_limpio[:200]


# Función helper para mensajes estilizados en modo claro
def show_message(parent, title, message, msg_type="info"):
    """
    Mostrar mensaje con estilos de modo claro
    msg_type: 'info', 'warning', 'error', 'success'
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)

    # Configurar icono según tipo
    if msg_type == "info":
        msg_box.setIcon(QMessageBox.Information)
    elif msg_type == "warning":
        msg_box.setIcon(QMessageBox.Warning)
    elif msg_type == "error":
        msg_box.setIcon(QMessageBox.Critical)
    elif msg_type == "success":
        msg_box.setIcon(QMessageBox.Information)

    # Estilo compacto y profesional
    msg_box.setStyleSheet("""
        QMessageBox {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
        }
        QMessageBox QLabel {
            color: #1e293b;
            font-size: 10pt;
            padding: 8px 12px;
        }
        QMessageBox QPushButton {
            background-color: #1a56db;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 6px 16px;
            min-width: 80px;
            font-size: 9pt;
            font-weight: 600;
        }
        QMessageBox QPushButton:hover {
            background-color: #1e40af;
        }
        QMessageBox QPushButton:pressed {
            background-color: #1e3a8a;
        }
    """)

    # Anchura mínima razonable para que no se estire demasiado
    msg_box.setMinimumWidth(360)

    return msg_box.exec()



# =============================================================================
# MAPEO DE COMANDOS POR DISPOSITIVO
# =============================================================================

MAPEO_DISPOSITIVOS = {
    "Cisco Catalyst 9200": {
        "prueba_1": {
            "descripcion": "show version, show inventory",
            "comandos": [
                {"comando": "show version", "espera": 2},
                {"comando": "show inventory", "espera": 2}
            ]
        },
        "prueba_2": {
            "descripcion": "show environment power",
            "repetir_por_fuentes": True,
            "comandos": [
                {"comando": "show environment power", "espera": 2}
            ]
        },
        "prueba_3": {
            "descripcion": "show environment fan",
            "repetir_por_ventiladores": True,
            "comandos": [
                {"comando": "show environment fan", "espera": 2}
            ]
        },
        "prueba_4": {
            "descripcion": "reload, enable, show version",
            "ejecutar_reload": True,
            "comandos": []  # El reload se maneja de forma especial
        },
        "prueba_5": {
            "descripcion": "show inventory, show interfaces",
            "comandos": [
                {"comando": "show inventory", "espera": 3},
                {"comando": "show interfaces", "espera": 5},
            ]
        }
    },

    "Cisco Catalyst 9300": {
        "prueba_1": {
            "descripcion": "show version, show inventory",
            "comandos": [
                {"comando": "show version", "espera": 2},
                {"comando": "show inventory", "espera": 2}
            ]
        },
        "prueba_2": {
            "descripcion": "show environment power",
            "repetir_por_fuentes": True,
            "comandos": [
                {"comando": "show environment power", "espera": 2}
            ]
        },
        "prueba_3": {
            "descripcion": "show environment fan",
            "repetir_por_ventiladores": True,
            "comandos": [
                {"comando": "show environment fan", "espera": 2}
            ]
        },
        "prueba_4": {
            "descripcion": "reload, enable, show version",
            "ejecutar_reload": True,
            "comandos": []  # Usa la misma lógica de reload que el 9200
        },
        "prueba_5": {
            "descripcion": "show inventory all, show interfaces ethernet",
            "comandos": [
                {"comando": "show inventory all", "espera": 3},
                {"comando": "show interfaces ethernet", "espera": 5}
            ]
        }
    },

    "Cisco Catalyst 9500": {
        "prueba_1": {
            "descripcion": "show version, show inventory",
            "comandos": [
                {"comando": "show version", "espera": 2},
                {"comando": "show inventory", "espera": 2}
            ]
        },
        "prueba_2": {
            "descripcion": "show environment status",
            "repetir_por_fuentes": True,
            "comandos": [
                {"comando": "show environment status", "espera": 2}
            ]
        },
        "prueba_3": {
            "descripcion": "show environment status",
            "repetir_por_ventiladores": True,
            "comandos": [
                {"comando": "show environment status", "espera": 2}
            ]
        },
        "prueba_4": {
            "descripcion": "reload, enable, show version",
            "ejecutar_reload": True,
            "comandos": []  # Usa la misma lógica de reload que el 9200
        },
        "prueba_5": {
            "descripcion": "show inventory all, show interface ethernet",
            "comandos": [
                {"comando": "show inventory all", "espera": 3},
                {"comando": "show interface ethernet", "espera": 5}
            ]
        }
    }
}


ESTADOS_QUE_NECESITAN_PAGO = {
    "SIN_SUSCRIPCION",  # Nunca ha contratado un plan
    "PENDIENTE_MP",     # Proceso iniciado en MP, aún no autorizado
    "PAUSADA",          # Suscripción pausada
    "CANCELADA",        # Suscripción cancelada
    "VENCIDA",          # Fecha de término ya pasó
    "EN_GRACIA",        # Periodo de gracia, pero queremos forzar pago
}

# =============================================================================
# FUNCIONES DEL SCRIPT CISCO 9200 - ADAPTADAS PARA LA INTERFAZ
# =============================================================================

# Configuración estándar para consola Cisco
BYTESIZE = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOPBITS = serial.STOPBITS_ONE
ESPERA_COMANDO = 1
ESPERA_RELOAD = 120  # 2 minutos para el reload (reducido de 3 minutos)


def abrir_conexion_serial(puerto: str, baudrate: int) -> serial.Serial:
    """
    Abre una conexión serial con el dispositivo Cisco y valida que haya un dispositivo real conectado.

    Args:
        puerto: Puerto serial (ej: COM3, /dev/ttyUSB0)
        baudrate: Velocidad de comunicación (9600, 115200, etc.)

    Returns:
        Objeto serial.Serial con conexión validada

    Raises:
        ValueError: Si puerto o baudrate son inválidos
        serial.SerialException: Si no se puede abrir el puerto
        DispositivoNoDetectadoError: Si el puerto abre pero no hay dispositivo Cisco
        TimeoutConexionError: Si el dispositivo no responde en el tiempo esperado
    """
    # Validar inputs
    if not validar_puerto_serial(puerto):
        logger.error(f"Puerto serial inválido: {puerto}")
        raise ValueError(f"Puerto serial inválido: {puerto}. Use formato COM1-99 o /dev/ttyUSB0-99")

    if not validar_baudrate(baudrate):
        logger.error(f"Baudrate inválido: {baudrate}")
        raise ValueError(f"Baudrate inválido: {baudrate}. Valores permitidos: {VALID_BAUDRATES}")

    conexion = None
    try:
        logger.info(f"Abriendo conexión serial en {puerto} a {baudrate} baudios...")
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

        logger.info(f"Puerto {puerto} abierto correctamente")

        # VALIDACIÓN CRÍTICA: Verificar que hay un dispositivo Cisco real conectado
        if not validar_dispositivo_conectado(conexion):
            conexion.close()
            raise DispositivoNoDetectadoError(
                f"El puerto {puerto} está disponible pero no hay un dispositivo Cisco respondiendo. "
                "Verifique que el cable esté conectado correctamente y que el dispositivo esté encendido."
            )

        logger.info(f"Dispositivo Cisco detectado y validado en {puerto}")
        return conexion

    except SerialException as error:
        logger.error(f"Error abriendo puerto serial {puerto}: {error}")
        if conexion and conexion.is_open:
            conexion.close()
        raise
    except (DispositivoNoDetectadoError, TimeoutConexionError):
        # Re-lanzar nuestras excepciones personalizadas
        raise
    except Exception as error:
        logger.error(f"Error inesperado abriendo conexión serial: {error}")
        if conexion and conexion.is_open:
            conexion.close()
        raise


def validar_dispositivo_conectado(conexion: serial.Serial) -> bool:
    """
    Valida que haya un dispositivo Cisco real conectado enviando comandos de prueba.

    Args:
        conexion: Conexión serial abierta

    Returns:
        True si hay un dispositivo Cisco respondiendo, False en caso contrario
    """
    try:
        logger.info("Validando dispositivo Cisco...")

        # Limpiar buffer
        conexion.reset_input_buffer()
        conexion.reset_output_buffer()

        # Enviar enters para despertar la consola
        for i in range(3):
            conexion.write(b"\r\n")
            time.sleep(0.3)

        # Leer respuesta inicial
        time.sleep(1)
        if conexion.in_waiting > 0:
            respuesta_inicial = conexion.read(conexion.in_waiting).decode('ascii', errors='ignore')
            logger.debug(f"Respuesta inicial: {respuesta_inicial[:100]}")

            # Verificar si hay un prompt
            if any(prompt in respuesta_inicial for prompt in CISCO_PROMPTS):
                logger.info("Prompt de Cisco detectado en respuesta inicial")
                return True

        # Si no hay prompt en respuesta inicial, enviar comando de prueba
        logger.info("Enviando comando de prueba: show version")
        conexion.reset_input_buffer()
        conexion.write(b"show version\n")

        # Esperar respuesta con timeout
        tiempo_inicio = time.time()
        respuesta_completa = ""

        while (time.time() - tiempo_inicio) < TIMEOUT_CONEXION_INICIAL:
            if conexion.in_waiting > 0:
                datos = conexion.read(conexion.in_waiting)
                respuesta_completa += datos.decode('ascii', errors='ignore')

                # Verificar si tenemos suficiente información
                if len(respuesta_completa) > 50:
                    break
            time.sleep(0.2)

        logger.debug(f"Respuesta de validación: {respuesta_completa[:200]}")

        # Verificar que la respuesta contenga palabras clave de Cisco
        if any(keyword in respuesta_completa for keyword in CISCO_KEYWORDS):
            logger.info("Dispositivo Cisco validado correctamente")
            return True

        # Verificar si hay prompt aunque no haya keywords
        if any(prompt in respuesta_completa for prompt in CISCO_PROMPTS):
            logger.warning("Prompt detectado pero sin keywords de Cisco. Aceptando conexión.")
            return True

        logger.warning(f"No se detectó dispositivo Cisco. Respuesta recibida: {respuesta_completa[:100]}")
        return False

    except Exception as error:
        logger.error(f"Error validando dispositivo conectado: {error}")
        return False


def verificar_conexion_activa(conexion: serial.Serial) -> bool:
    """
    Verifica que la conexión serial siga activa enviando Enter y esperando respuesta.

    En Windows, write/flush/is_open pueden NO fallar incluso si el cable está desconectado.
    La ÚNICA forma confiable es: enviar comando → esperar respuesta → si no hay respuesta = desconectado

    Args:
        conexion: Objeto de conexión serial

    Returns:
        True si la conexión está activa y el dispositivo responde, False en caso contrario
    """
    try:
        if not conexion:
            logger.error("[VERIFICAR] Conexión es None")
            return False

        if not conexion.is_open:
            logger.error("[VERIFICAR] Conexión serial cerrada (is_open = False)")
            return False

        # ESTRATEGIA DEFINITIVA: Enviar Enter y ESPERAR respuesta
        # Si el dispositivo está conectado, SIEMPRE responde algo (eco, prompt, etc.)
        try:
            # Guardar configuración original
            timeout_original = conexion.timeout

            # Timeout corto para detección rápida (1 segundo máximo)
            conexion.timeout = 1.0

            # Limpiar buffer de entrada para no confundir respuestas anteriores
            try:
                if conexion.in_waiting > 0:
                    conexion.read(conexion.in_waiting)
            except:
                pass

            # Enviar Enter
            try:
                bytes_written = conexion.write(b"\r\n")
                if bytes_written == 0:
                    logger.error("[VERIFICAR] write() retornó 0 bytes - puerto no acepta escritura")
                    conexion.timeout = timeout_original
                    return False

                # Flush para asegurar que se envía
                conexion.flush()
                logger.debug("[VERIFICAR] Enter enviado, esperando respuesta...")

            except (OSError, SerialException, IOError) as e:
                logger.error(f"[VERIFICAR] Error en write/flush: {type(e).__name__} - {e}")
                conexion.timeout = timeout_original
                return False

            # Esperar un momento a que el dispositivo procese y responda
            time.sleep(0.7)

            # CRÍTICO: Verificar si hay respuesta
            # Un dispositivo Cisco SIEMPRE responde algo al Enter (mínimo un eco o prompt)
            try:
                bytes_disponibles = conexion.in_waiting
                logger.debug(f"[VERIFICAR] Bytes disponibles para leer: {bytes_disponibles}")

                if bytes_disponibles > 0:
                    # HAY RESPUESTA = Dispositivo está conectado y funcionando
                    respuesta = conexion.read(bytes_disponibles)
                    logger.debug(f"[VERIFICAR] Dispositivo respondió ({len(respuesta)} bytes): {respuesta[:50]}")
                    conexion.timeout = timeout_original
                    return True
                else:
                    # NO HAY RESPUESTA después de 0.7 segundos
                    # Esto significa que el dispositivo NO está conectado o NO responde
                    logger.error("[VERIFICAR] Sin respuesta del dispositivo - probablemente desconectado")
                    conexion.timeout = timeout_original
                    return False

            except (OSError, SerialException, IOError) as e:
                logger.error(f"[VERIFICAR] Error leyendo respuesta: {type(e).__name__} - {e}")
                conexion.timeout = timeout_original
                return False

        except (OSError, SerialException, IOError) as e:
            logger.error(f"[VERIFICAR] Error general en verificación: {type(e).__name__} - {e}")
            return False

    except Exception as error:
        logger.error(f"[VERIFICAR] Error inesperado: {type(error).__name__} - {error}")
        return False


def cerrar_conexion_serial(conexion: Optional[serial.Serial]) -> None:
    """
    Cierra la conexión serial de forma segura.

    Args:
        conexion: Objeto de conexión serial o None
    """
    try:
        if conexion and conexion.is_open:
            logger.info("Cerrando conexión serial...")
            conexion.close()
            logger.info("Conexión serial cerrada correctamente")
    except Exception as error:
        logger.error(f"Error cerrando conexión serial: {error}")
        
def limpiar_caracteres_control(texto):
    """
    Elimina caracteres de control no imprimibles de la salida,
    dejando solo saltos de línea, retorno de carro y tabulaciones.
    Esto evita que en el archivo aparezcan cuadros raros.
    """
    resultado = []
    for ch in texto:
        codigo = ord(ch)
        # Permitimos salto de línea, retorno de carro y tabulación
        if ch in ("\n", "\r", "\t"):
            resultado.append(ch)
        # Permitimos caracteres imprimibles estándar
        elif 32 <= codigo <= 126:
            resultado.append(ch)
        # El resto de caracteres de control se descarta
    return "".join(resultado)

def leer_respuesta_completa(conexion: serial.Serial, timeout_total: int = 10) -> str:
    """
    Lee la respuesta completa del dispositivo hasta que no haya más datos.

    Args:
        conexion: Conexión serial activa
        timeout_total: Timeout máximo en segundos

    Returns:
        Respuesta completa del dispositivo

    Raises:
        DispositivoDesconectadoError: Si el dispositivo se desconecta durante la lectura
        TimeoutConexionError: Si no se recibe respuesta en el tiempo esperado
    """
    respuesta_completa = ""
    tiempo_inicio = time.time()
    timeout_alcanzado = False
    ultimo_check_conexion = time.time()

    try:
        while True:
            tiempo_transcurrido = time.time() - tiempo_inicio

            if tiempo_transcurrido > timeout_total:
                timeout_alcanzado = True
                break

            # CRÍTICO: Verificar conexión cada 1 segundo para detectar desconexiones rápido
            # Pero no en cada iteración para no sobrecargar
            if time.time() - ultimo_check_conexion > 1.0:
                if not verificar_conexion_activa(conexion):
                    logger.error("Dispositivo desconectado durante lectura de respuesta")
                    raise DispositivoDesconectadoError(
                        "El dispositivo se desconectó durante la operación. "
                        "Verifique el cable y la conexión física."
                    )
                ultimo_check_conexion = time.time()

            if conexion.in_waiting > 0:
                try:
                    datos = conexion.read(conexion.in_waiting)
                except (OSError, SerialException) as e:
                    logger.error(f"Error leyendo datos del puerto: {e}")
                    raise DispositivoDesconectadoError(f"Error leyendo del puerto serial: {e}")

                try:
                    texto = datos.decode("ascii", errors="ignore")
                except UnicodeDecodeError:
                    logger.warning("Error decodificando como ASCII, intentando latin-1")
                    texto = datos.decode("latin-1", errors="ignore")

                # Limpiar caracteres de control no imprimibles
                texto = limpiar_caracteres_control(texto)

                respuesta_completa += texto
                tiempo_inicio = time.time()  # Resetear timeout cuando hay datos
            else:
                time.sleep(0.1)

                if conexion.in_waiting == 0:
                    time.sleep(0.5)
                    if conexion.in_waiting == 0:
                        # CRÍTICO: Antes de asumir que terminó, verificar que la conexión está activa
                        # Si no hay datos Y la conexión está muerta, es un error no un fin normal
                        if not verificar_conexion_activa(conexion):
                            logger.error("Conexión perdida mientras esperaba datos")
                            raise DispositivoDesconectadoError(
                                "La conexión se perdió. No se recibieron más datos del dispositivo."
                            )
                        # Si la conexión está activa pero no hay datos, es fin normal
                        break

    except SerialException as error:
        logger.error(f"Error serial durante lectura: {error}")
        raise DispositivoDesconectadoError(f"Error de comunicación serial: {error}")
    except DispositivoDesconectadoError:
        # Re-lanzar nuestra excepción personalizada
        raise
    except Exception as error:
        logger.error(f"Error inesperado leyendo respuesta: {error}")
        raise

    # Advertir si no se recibió nada y hubo timeout
    if not respuesta_completa and timeout_alcanzado:
        logger.warning(f"Timeout de {timeout_total}s alcanzado sin recibir datos")
        raise TimeoutConexionError(
            f"No se recibió respuesta del dispositivo después de {timeout_total} segundos. "
            "El dispositivo puede estar desconectado o no responde."
        )

    return respuesta_completa



def enviar_comando(conexion: serial.Serial, comando: str, espera: int = ESPERA_COMANDO) -> str:
    """
    Envía un comando al dispositivo y espera la respuesta.

    Args:
        conexion: Conexión serial activa
        comando: Comando a enviar
        espera: Tiempo de espera en segundos antes de leer respuesta

    Returns:
        Respuesta del dispositivo

    Raises:
        DispositivoDesconectadoError: Si el dispositivo se desconecta
        TimeoutConexionError: Si no hay respuesta en el tiempo esperado
    """
    try:
        # Verificar conexión activa antes de enviar
        if not verificar_conexion_activa(conexion):
            logger.error("Conexión no activa antes de enviar comando")
            raise DispositivoDesconectadoError("La conexión se perdió antes de enviar el comando")

        logger.debug(f"Enviando comando: {comando}")
        conexion.reset_input_buffer()
        comando_bytes = (comando + "\n").encode('ascii')
        conexion.write(comando_bytes)
        time.sleep(espera)

        # Verificar conexión activa después de enviar
        if not verificar_conexion_activa(conexion):
            logger.error("Conexión perdida después de enviar comando")
            raise DispositivoDesconectadoError("La conexión se perdió después de enviar el comando")

        respuesta = leer_respuesta_completa(conexion)
        logger.debug(f"Respuesta recibida ({len(respuesta)} caracteres)")
        return respuesta

    except SerialException as error:
        logger.error(f"Error serial enviando comando '{comando}': {error}")
        raise DispositivoDesconectadoError(f"Error de comunicación: {error}")
    except (DispositivoDesconectadoError, TimeoutConexionError):
        # Re-lanzar nuestras excepciones personalizadas
        raise
    except Exception as error:
        logger.error(f"Error inesperado enviando comando '{comando}': {error}")
        raise


def manejar_more_prompt(conexion, respuesta):
    """Maneja el prompt '--More--' que aparece en salidas largas de Cisco"""
    respuesta_total = respuesta

    while "--More--" in respuesta_total:
        conexion.write(b" ")
        time.sleep(0.5)
        nueva_respuesta = leer_respuesta_completa(conexion, timeout_total=5)
        respuesta_total = respuesta_total.replace("--More--", "")
        respuesta_total += nueva_respuesta

    return respuesta_total


def ejecutar_comando_completo_con_prompt(conexion, comando, espera=ESPERA_COMANDO):
    """
    Ejecuta un comando capturando EXACTAMENTE lo que se ve en el CLI
    Incluye los prompts antes del comando para validación
    """
    # CRÍTICO: Verificar conexión ANTES de ejecutar comando
    if not verificar_conexion_activa(conexion):
        logger.error(f"Conexión perdida antes de ejecutar comando: {comando}")
        raise DispositivoDesconectadoError(
            f"La conexión se perdió antes de ejecutar el comando '{comando}'. "
            "Verifique el cable y la conexión física."
        )

    # PASO 1: Enviar 2 enters para obtener el prompt (validación)
    conexion.write(b"\n")
    time.sleep(0.3)
    respuesta_enter1 = leer_respuesta_completa(conexion, timeout_total=2)

    conexion.write(b"\n")
    time.sleep(0.3)
    respuesta_enter2 = leer_respuesta_completa(conexion, timeout_total=2)

    # PASO 2: Enviar el comando real
    conexion.reset_input_buffer()
    comando_bytes = (comando + "\n").encode('ascii')
    conexion.write(comando_bytes)
    time.sleep(espera)

    # PASO 3: Leer la respuesta completa
    respuesta_comando = leer_respuesta_completa(conexion)

    # PASO 4: Manejar paginación --More--
    respuesta_comando = manejar_more_prompt(conexion, respuesta_comando)

    # PASO 5: Combinar todo - EXACTAMENTE como se vería en el CLI
    respuesta_completa = respuesta_enter1 + respuesta_enter2 + respuesta_comando

    return respuesta_completa


def ejecutar_comando_completo(conexion, comando, espera=ESPERA_COMANDO):
    """Ejecuta un comando y maneja automáticamente el paginado --More--"""
    # CRÍTICO: Verificar conexión ANTES de ejecutar comando
    if not verificar_conexion_activa(conexion):
        logger.error(f"Conexión perdida antes de ejecutar comando: {comando}")
        raise DispositivoDesconectadoError(
            f"La conexión se perdió antes de ejecutar el comando '{comando}'. "
            "Verifique el cable y la conexión física."
        )

    respuesta = enviar_comando(conexion, comando, espera)
    respuesta = manejar_more_prompt(conexion, respuesta)
    return respuesta


def despertar_consola(conexion):
    """'Despierta' la consola enviando Enter para obtener el prompt"""
    for _ in range(3):
        conexion.write(b"\r\n")
        time.sleep(0.5)

    respuesta = leer_respuesta_completa(conexion, timeout_total=5)
    return respuesta


def leer_respuesta_permisiva(conexion: serial.Serial, timeout_total: int = 10) -> str:
    """
    Lee la respuesta completa del dispositivo SIN lanzar excepciones por desconexión.

    Esta versión es para usar durante/después del reload cuando la desconexión es NORMAL.

    Args:
        conexion: Conexión serial activa
        timeout_total: Timeout máximo en segundos

    Returns:
        Respuesta completa del dispositivo (puede estar vacía si no hay datos)
    """
    respuesta_completa = ""
    tiempo_inicio = time.time()

    try:
        while True:
            tiempo_transcurrido = time.time() - tiempo_inicio

            if tiempo_transcurrido > timeout_total:
                # No lanzar excepción, simplemente retornar lo que se tenga
                break

            if conexion.in_waiting > 0:
                try:
                    datos = conexion.read(conexion.in_waiting)
                    texto = datos.decode("ascii", errors="ignore")
                    texto = limpiar_caracteres_control(texto)
                    respuesta_completa += texto
                    tiempo_inicio = time.time()  # Resetear timeout cuando hay datos
                except (OSError, SerialException):
                    # Error leyendo, simplemente continuar
                    break
            else:
                time.sleep(0.1)

                if conexion.in_waiting == 0:
                    time.sleep(0.5)
                    if conexion.in_waiting == 0:
                        # No hay más datos, terminar normalmente
                        break

    except Exception:
        # Cualquier error, retornar lo que se tenga
        pass

    return respuesta_completa


def ejecutar_comando_sin_verificacion(conexion: serial.Serial, comando: str, espera: int = 2) -> str:
    """
    Ejecuta un comando SIN verificar conexión antes/después.

    Uso exclusivo para contextos post-reload donde la verificación puede fallar
    aunque la conexión esté realmente funcionando.

    Args:
        conexion: Conexión serial
        comando: Comando a enviar
        espera: Tiempo de espera antes de leer respuesta

    Returns:
        Respuesta del dispositivo (puede estar vacía)
    """
    try:
        logger.debug(f"[SIN_VERIFICACION] Enviando comando: {comando}")

        # NO hacer reset_input_buffer() - podría haber datos valiosos
        comando_bytes = (comando + "\n").encode('ascii')
        conexion.write(comando_bytes)
        time.sleep(espera)

        # Usar versión permisiva de lectura
        respuesta = leer_respuesta_permisiva(conexion, timeout_total=10)
        logger.debug(f"[SIN_VERIFICACION] Respuesta recibida ({len(respuesta)} caracteres)")
        return respuesta

    except Exception as error:
        logger.error(f"[SIN_VERIFICACION] Error enviando comando: {error}")
        return ""


def ejecutar_comando_completo_sin_verificacion(conexion: serial.Serial, comando: str, espera: int = 2) -> str:
    """
    Ejecuta un comando capturando EXACTAMENTE lo que se ve en el CLI (con prompts),
    pero SIN verificar conexión (para uso post-reload).

    Esta es la versión "sin verificación estricta" de ejecutar_comando_completo_con_prompt().
    Captura:
    1. Los prompts previos (2 enters)
    2. El comando enviado con su eco
    3. La respuesta completa del dispositivo

    Args:
        conexion: Conexión serial
        comando: Comando a enviar
        espera: Tiempo de espera antes de leer respuesta

    Returns:
        Respuesta completa incluyendo prompts y eco (como se vería en el CLI)
    """
    try:
        logger.debug(f"[COMPLETO_SIN_VERIFICACION] Ejecutando comando: {comando}")

        # PASO 1: Enviar 2 enters para obtener el prompt (validación)
        conexion.write(b"\n")
        time.sleep(0.3)
        respuesta_enter1 = leer_respuesta_permisiva(conexion, timeout_total=2)

        conexion.write(b"\n")
        time.sleep(0.3)
        respuesta_enter2 = leer_respuesta_permisiva(conexion, timeout_total=2)

        # PASO 2: Enviar el comando real
        # NO resetear buffer - podría haber datos valiosos
        comando_bytes = (comando + "\n").encode('ascii')
        conexion.write(comando_bytes)
        time.sleep(espera)

        # PASO 3: Leer la respuesta completa
        respuesta_comando = leer_respuesta_permisiva(conexion, timeout_total=10)

        # PASO 4: Manejar paginación --More-- si existe
        # Usar una versión simple sin excepciones
        respuesta_total = respuesta_comando
        intentos_more = 0
        max_intentos_more = 20

        while "--More--" in respuesta_total and intentos_more < max_intentos_more:
            try:
                conexion.write(b" ")
                time.sleep(0.5)
                nueva_respuesta = leer_respuesta_permisiva(conexion, timeout_total=5)
                respuesta_total = respuesta_total.replace("--More--", "")
                respuesta_total += nueva_respuesta
                intentos_more += 1
            except:
                break

        # PASO 5: Combinar todo - EXACTAMENTE como se vería en el CLI
        respuesta_completa = respuesta_enter1 + respuesta_enter2 + respuesta_total

        logger.debug(f"[COMPLETO_SIN_VERIFICACION] Respuesta capturada ({len(respuesta_completa)} caracteres)")
        return respuesta_completa

    except Exception as error:
        logger.error(f"[COMPLETO_SIN_VERIFICACION] Error ejecutando comando: {error}")
        return ""


def entrar_modo_enable_sin_verificacion(conexion: serial.Serial, password: str = None) -> str:
    """
    Entra al modo enable capturando TODO el flujo del CLI (incluyendo Password:) en una sola operación.

    Esta función maneja el flujo completo de enable con password SIN verificaciones estrictas,
    capturando EXACTAMENTE lo que se ve en el CLI real.

    VERSIÓN SIMPLIFICADA: Lectura manual TOTAL sin usar leer_respuesta_permisiva()

    Args:
        conexion: Conexión serial
        password: Contraseña de enable (opcional)

    Returns:
        String con TODO el output del CLI (prompts + comandos + respuestas)
    """
    try:
        logger.debug("[ENABLE_SIN_VERIFICACION] ===== INICIO ENABLE =====")

        respuesta_total = ""
        password_enviado = False

        # PASO 1: Enviar primer Enter y leer
        logger.debug("[ENABLE_SIN_VERIFICACION] Enviando Enter 1")
        conexion.write(b"\n")
        time.sleep(0.5)

        # Leer manualmente
        for _ in range(10):  # Intentar leer por 3 segundos (10 * 0.3)
            if conexion.in_waiting > 0:
                datos = conexion.read(conexion.in_waiting)
                texto = datos.decode('ascii', errors='ignore')
                respuesta_total += texto
                logger.debug(f"[ENABLE_SIN_VERIFICACION] Enter1: +{len(datos)} bytes")
                break
            time.sleep(0.3)

        # PASO 2: Enviar segundo Enter y leer
        logger.debug("[ENABLE_SIN_VERIFICACION] Enviando Enter 2")
        conexion.write(b"\n")
        time.sleep(0.5)

        for _ in range(10):
            if conexion.in_waiting > 0:
                datos = conexion.read(conexion.in_waiting)
                texto = datos.decode('ascii', errors='ignore')
                respuesta_total += texto
                logger.debug(f"[ENABLE_SIN_VERIFICACION] Enter2: +{len(datos)} bytes")
                break
            time.sleep(0.3)

        # PASO 3: Enviar comando enable
        logger.debug("[ENABLE_SIN_VERIFICACION] Enviando: enable")
        conexion.write(b"enable\n")

        # CRÍTICO: Esperar para que el switch procese el comando ANTES de empezar a leer
        logger.debug("[ENABLE_SIN_VERIFICACION] Esperando 0.8s para que el switch procese...")
        time.sleep(0.8)

        # PASO 4: LECTURA CONTINUA con detección reactiva de Password:
        tiempo_inicio = time.time()
        tiempo_ultima_lectura = time.time()
        timeout_total = 25  # Timeout generoso

        logger.debug("[ENABLE_SIN_VERIFICACION] Iniciando lectura continua...")

        iteracion = 0
        while time.time() - tiempo_inicio < timeout_total:
            iteracion += 1

            # Logging periódico cada 20 iteraciones
            if iteracion % 20 == 0:
                logger.debug(f"[ENABLE_SIN_VERIFICACION] Iteración {iteracion}, in_waiting={conexion.in_waiting}, capturados={len(respuesta_total)} chars")

            # Chequear datos disponibles
            if conexion.in_waiting > 0:
                try:
                    # Leer TODO lo disponible
                    datos = conexion.read(conexion.in_waiting)
                    texto = datos.decode('ascii', errors='ignore')
                    respuesta_total += texto
                    tiempo_ultima_lectura = time.time()

                    logger.debug(f"[ENABLE_SIN_VERIFICACION] +{len(datos)} bytes: {repr(texto)}")

                    # DETECCIÓN REACTIVA: Si vemos Password: y no hemos enviado password
                    if password and not password_enviado:
                        if "Password:" in respuesta_total or "password:" in respuesta_total.lower():
                            logger.debug("[ENABLE_SIN_VERIFICACION] *** DETECTADO 'Password:' ***")
                            logger.debug("[ENABLE_SIN_VERIFICACION] Esperando 0.3s antes de enviar password...")
                            time.sleep(0.3)

                            logger.debug(f"[ENABLE_SIN_VERIFICACION] Enviando password: '{password}'")
                            conexion.write((password + "\n").encode('ascii'))
                            password_enviado = True

                            logger.debug("[ENABLE_SIN_VERIFICACION] Password enviado. Continuando lectura...")
                            # Esperar respuesta después de password
                            time.sleep(1.5)
                            continue  # Volver a leer inmediatamente

                    # DETECCIÓN DE FINALIZACIÓN: Si vemos #
                    if "#" in respuesta_total:
                        logger.debug("[ENABLE_SIN_VERIFICACION] Detectado '#' en respuesta")
                        # Esperar un momento para asegurar que no hay más datos
                        logger.debug("[ENABLE_SIN_VERIFICACION] Esperando 1.5s para confirmar finalización...")
                        time.sleep(1.5)

                        # Verificar que no hay más datos
                        if conexion.in_waiting == 0:
                            logger.debug("[ENABLE_SIN_VERIFICACION] Confirmado: Sin más datos después de #, finalizando")
                            break
                        else:
                            logger.debug(f"[ENABLE_SIN_VERIFICACION] Aún hay {conexion.in_waiting} bytes pendientes, continuando lectura...")

                except Exception as e:
                    logger.error(f"[ENABLE_SIN_VERIFICACION] Error en lectura: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    break
            else:
                # Sin datos, esperar
                time.sleep(0.3)

                # Si llevamos mucho tiempo sin recibir datos, salir
                # IMPORTANTE: Ser MÁS paciente - esperar 5 segundos de silencio antes de salir
                tiempo_sin_datos = time.time() - tiempo_ultima_lectura
                if tiempo_sin_datos > 5.0:
                    logger.debug(f"[ENABLE_SIN_VERIFICACION] Sin datos por {tiempo_sin_datos:.1f}s, finalizando")
                    break

        # PASO 5: Limpiar caracteres de control
        respuesta_total = limpiar_caracteres_control(respuesta_total)

        logger.debug(f"[ENABLE_SIN_VERIFICACION] ===== FIN ENABLE =====")
        logger.debug(f"[ENABLE_SIN_VERIFICACION] Total capturado: {len(respuesta_total)} caracteres")
        logger.debug(f"[ENABLE_SIN_VERIFICACION] Contenido COMPLETO:\n{repr(respuesta_total)}")

        return respuesta_total

    except Exception as error:
        logger.error(f"[ENABLE_SIN_VERIFICACION] ERROR CRÍTICO: {error}")
        import traceback
        logger.error(traceback.format_exc())
        return ""


def estabilizar_consola_post_reload(conexion: serial.Serial, max_intentos: int = 10) -> bool:
    """
    Estabiliza la consola después del reload enviando Enters hasta obtener un prompt estable.

    Esta función se asegura de que el switch haya terminado de enviar todos los mensajes
    de boot y esté listo para recibir comandos.

    Args:
        conexion: Conexión serial
        max_intentos: Número máximo de intentos

    Returns:
        True si se estabilizó, False si no
    """
    logger.info("[ESTABILIZAR] Iniciando estabilización de consola post-reload")

    prompts_estables_consecutivos = 0
    prompts_requeridos = 2  # Necesitamos ver el prompt al menos 2 veces seguidas

    for intento in range(max_intentos):
        try:
            # Enviar Enter
            conexion.write(b"\r\n")
            time.sleep(1.5)  # Espera generosa

            # Leer respuesta
            if conexion.in_waiting > 0:
                datos = conexion.read(conexion.in_waiting)
                respuesta = datos.decode('ascii', errors='ignore')

                # Buscar prompts de usuario (>) o privilegiado (#)
                # Pero asegurarse de que estén al FINAL de la respuesta (prompt real)
                lineas = respuesta.strip().split('\n')
                ultima_linea = lineas[-1] if lineas else ""

                if ultima_linea.endswith('>') or ultima_linea.endswith('#'):
                    prompts_estables_consecutivos += 1
                    logger.debug(f"[ESTABILIZAR] Prompt detectado ({prompts_estables_consecutivos}/{prompts_requeridos}): '{ultima_linea[-20:]}'")

                    if prompts_estables_consecutivos >= prompts_requeridos:
                        logger.info(f"[ESTABILIZAR] Consola estabilizada después de {intento + 1} intentos")
                        return True
                else:
                    # No hay prompt al final, reiniciar contador
                    prompts_estables_consecutivos = 0
            else:
                # Sin respuesta, reiniciar contador
                prompts_estables_consecutivos = 0

            time.sleep(2)

        except Exception as e:
            logger.warning(f"[ESTABILIZAR] Error en intento {intento + 1}: {e}")
            prompts_estables_consecutivos = 0
            continue

    logger.warning("[ESTABILIZAR] No se pudo estabilizar la consola completamente")
    return False


def entrar_modo_enable(conexion, password):
    """Entra al modo privilegiado (enable) del dispositivo"""
    respuesta = enviar_comando(conexion, "enable", espera=1)

    if "Password:" in respuesta or "password:" in respuesta.lower():
        respuesta = enviar_comando(conexion, password, espera=1)

    if "#" in respuesta:
        return True
    else:
        return True  # Continuar de todas formas


def configurar_terminal(conexion):
    """Configura el terminal para evitar paginación y mejorar la salida"""
    ejecutar_comando_completo(conexion, "terminal length 0")
    ejecutar_comando_completo(conexion, "terminal width 512")


def contar_fuentes_poder(salida_show_inventory):
    """
    Cuenta el número de fuentes de poder según 'show inventory'
    Busca líneas que contengan PID de fuentes de poder o descripciones
    """
    # Contar líneas con PID de fuentes de poder (PWR-, C9K-PWR, etc.)
    # o descripciones de Power Supply
    patron_pid = re.compile(r'PID:\s*(PWR-[^\s,]+|C9K-PWR[^\s,]+)', re.IGNORECASE)
    patron_desc = re.compile(r'DESCR:.*Power\s+Supply', re.IGNORECASE)
    patron_name = re.compile(r'NAME:.*Power\s+Supply', re.IGNORECASE)

    pids = patron_pid.findall(salida_show_inventory)
    descs = patron_desc.findall(salida_show_inventory)
    names = patron_name.findall(salida_show_inventory)

    # Usar el máximo entre los tres métodos
    cantidad = max(len(pids), len(descs), len(names))

    # Si no se encuentra ninguna, asumir 1
    if cantidad == 0:
        cantidad = 1

    return cantidad


def contar_ventiladores(salida_show_inventory):
    """
    Cuenta el número de ventiladores según 'show inventory'
    Busca líneas que contengan PID de ventiladores o descripciones
    """
    # Contar líneas con PID de ventiladores o descripciones
    # Ejemplos: C9200-FAN-1, FAN-1, etc.
    patron_pid = re.compile(r'PID:\s*([^\s,]*FAN[^\s,]*)', re.IGNORECASE)
    patron_desc = re.compile(r'DESCR:.*Fan\s+(Tray|Module|Assembly)', re.IGNORECASE)
    patron_name = re.compile(r'NAME:.*Fan', re.IGNORECASE)

    pids = patron_pid.findall(salida_show_inventory)
    descs = patron_desc.findall(salida_show_inventory)
    names = patron_name.findall(salida_show_inventory)

    # Usar el máximo entre los tres métodos
    cantidad = max(len(pids), len(descs), len(names))

    # Si no se encuentra ninguna, asumir 1
    if cantidad == 0:
        cantidad = 1

    return cantidad


def extraer_info_dispositivo_9200(lines):
    """Extrae modelo, serial y versión del archivo de salida (igual que __init__.py)"""
    modelo, serial, version = None, None, None

    patron_inicio_prueba_1 = re.compile(r'.*[#>]\s*INICIO\s+PRUEBA\s+1\b', re.IGNORECASE)
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
            for siguiente_linea in lines[lines.index(line):]:
                version_match = re.search(r'Version\s+(\S+)', siguiente_linea, re.IGNORECASE)
                if version_match:
                    version = version_match.group(1).strip()
                    break
            break

    return modelo, serial, version


# =============================================================================
# THREAD PARA EJECUTAR LAS PRUEBAS
# =============================================================================

class TestThread(QThread):
    """Thread para ejecutar las pruebas sin bloquear la UI"""
    log_signal = Signal(str, str)  # (mensaje, tipo)
    finished_signal = Signal(bool, str)  # (success, archivo_salida)
    mostrar_popup_signal = Signal(str, str)  # (titulo, mensaje) - para mostrar popups desde el thread

    def __init__(self, puerto, baudrate, password_enable, num_ventiladores, num_fuentes, ejecutar_prueba5, modelo_dispositivo, permitir_desconexion, parent_window):
        super().__init__()
        self.puerto = puerto
        self.baudrate = baudrate
        self.password_enable = password_enable if password_enable else ""
        self.num_ventiladores = num_ventiladores
        self.num_fuentes = num_fuentes
        self.ejecutar_prueba5 = ejecutar_prueba5
        self.modelo_dispositivo = modelo_dispositivo
        self.permitir_desconexion = permitir_desconexion
        self.parent_window = parent_window
        self.mapeo = MAPEO_DISPOSITIVOS.get(modelo_dispositivo, {})
        self.archivo_salida = ""
        self.contenido_archivo = []
        self.popup_confirmado = False

        # Conectar señal para popups
        self.mostrar_popup_signal.connect(self._mostrar_popup_bloqueante)

    def log(self, mensaje, tipo="info"):
        """Emite señal de log a la UI"""
        self.log_signal.emit(mensaje, tipo)

    def _mostrar_popup_bloqueante(self, titulo, mensaje):
        """Muestra un popup y espera a que el usuario presione OK"""
        msg_box = QMessageBox(self.parent_window)
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.setStandardButtons(QMessageBox.Ok)

        # Determinar el icono según el tipo de acción
        if "Desconecte" in mensaje or "desconectar" in mensaje.lower():
            icon_color = "#f59e0b"
            msg_box.setIcon(QMessageBox.Warning)
        elif "Reconecte" in mensaje or "reconectar" in mensaje.lower():
            icon_color = "#10b981"
            msg_box.setIcon(QMessageBox.Information)
        elif "Verifique" in mensaje or "verificar" in mensaje.lower():
            icon_color = "#3b82f6"
            msg_box.setIcon(QMessageBox.Information)
        else:
            icon_color = "#3b82f6"
            msg_box.setIcon(QMessageBox.Information)

        # Estilo compacto y profesional para los pop ups de prueba
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: #ffffff;
                border: 1px solid {icon_color};
                border-radius: 6px;
            }}
            QLabel {{
                color: #1e293b;
                font-size: 10pt;
                padding: 8px 12px;
            }}
            QPushButton {{
                background-color: #1a56db;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 18px;
                min-width: 90px;
                font-size: 9pt;
                font-weight: 600;
                margin: 6px;
            }}
            QPushButton:hover {{
                background-color: #1e40af;
            }}
            QPushButton:pressed {{
                background-color: #1e3a8a;
            }}
        """)

        # Evita que el diálogo se estire demasiado a lo ancho
        msg_box.setMinimumWidth(360)

        msg_box.exec()
        self.popup_confirmado = True


    def mostrar_popup(self, titulo, mensaje):
        """Solicita mostrar un popup y espera confirmación"""
        self.popup_confirmado = False
        self.mostrar_popup_signal.emit(titulo, mensaje)

        # Esperar a que el usuario presione OK
        while not self.popup_confirmado:
            time.sleep(0.1)

    def escribir_en_archivo(self, texto):
        """Agrega texto al contenido del archivo"""
        self.contenido_archivo.append(texto)

    def escribir_inicio_prueba(self, numero_prueba, descripcion):
        """Escribe el marcador de inicio de una prueba"""
        texto = f"\n{'#' * 80}\n"
        texto += f"### INICIO PRUEBA {numero_prueba}: {descripcion}\n"
        texto += f"### Hora: {datetime.now().strftime('%H:%M:%S')}\n"
        texto += f"{'#' * 80}\n\n"
        self.escribir_en_archivo(texto)
        self.log(f"PRUEBA {numero_prueba} INICIANDO: {descripcion}", "info")

    def escribir_fin_prueba(self, numero_prueba):
        """Escribe el marcador de fin de una prueba"""
        texto = f"\n{'#' * 80}\n"
        texto += f"### FIN PRUEBA {numero_prueba}\n"
        texto += f"### Hora: {datetime.now().strftime('%H:%M:%S')}\n"
        texto += f"{'#' * 80}\n\n"
        self.escribir_en_archivo(texto)
        self.log(f"PRUEBA {numero_prueba} FINALIZADA", "success")

    def escribir_comando_resultado(self, resultado):
        """
        Escribe el resultado del comando exactamente como viene del CLI
        Sin modificaciones, sin agregar nada - copy/paste directo

        Args:
            resultado: La respuesta completa del dispositivo (ya incluye prompt + comando + output)
        """
        # Escribir EXACTAMENTE como viene del CLI - sin tocar nada
        self.escribir_en_archivo(resultado)
    def ejecutar_prueba_generica(self, conexion, numero_prueba, config_prueba):
        """Ejecuta una prueba genérica basada en la configuración del mapeo"""
        if not config_prueba or not config_prueba.get("comandos"):
            self.log(f"Prueba {numero_prueba}: Sin comandos configurados", "warning")
            self.escribir_inicio_prueba(numero_prueba, config_prueba.get("descripcion", "Sin configuración"))
            self.escribir_en_archivo(f"\n*** PRUEBA {numero_prueba} SIN COMANDOS CONFIGURADOS ***\n")
            self.escribir_fin_prueba(numero_prueba)
            return None

        descripcion = config_prueba.get("descripcion", f"Prueba {numero_prueba}")
        self.escribir_inicio_prueba(numero_prueba, descripcion)

        resultado_acumulado = ""

        for cmd_config in config_prueba.get("comandos", []):
            comando = cmd_config.get("comando")
            espera = cmd_config.get("espera", ESPERA_COMANDO)

            self.log(f"Ejecutando: {comando}", "command")
            # Usar la nueva función que captura TODO incluyendo prompts
            resultado = ejecutar_comando_completo_con_prompt(conexion, comando, espera=espera)

            # Escribir EXACTAMENTE lo que viene del CLI - sin tocar nada
            self.escribir_comando_resultado(resultado)
            resultado_acumulado += resultado

        self.escribir_fin_prueba(numero_prueba)
        return resultado_acumulado
    
    def ejecutar_prueba_repetitiva(self, conexion, numero_prueba, config_prueba, cantidad_repeticiones, tipo="", nombre_componente="componente"):
        """
        Ejecuta una prueba que se repite varias veces (fuentes/ventiladores)

        Args:
            conexion: Conexión serial
            numero_prueba: Número de la prueba
            config_prueba: Configuración de la prueba
            cantidad_repeticiones: Cuántas veces repetir
            tipo: Descripción del tipo (ej: "fuente(s)", "ventilador(es)")
            nombre_componente: Nombre del componente para los popups (ej: "ventilador", "fuente de poder")
        """
        if not config_prueba or not config_prueba.get("comandos"):
            self.log(f"Prueba {numero_prueba}: Sin comandos configurados", "warning")
            return

        descripcion = config_prueba.get("descripcion", f"Prueba {numero_prueba}")

        # Verificar si se permite desconexión Y hay más de 1 componente
        if self.permitir_desconexion and cantidad_repeticiones > 1:
            # MODO CON DESCONEXIÓN
            self.escribir_inicio_prueba(
                numero_prueba,
                f"{descripcion} - Prueba con desconexión ({cantidad_repeticiones} {tipo})"
            )

            # PASO 1: Verificar que todos estén conectados
            self.log(f"Solicitando verificación: Todos los {tipo} conectados", "warning")
            self.mostrar_popup(
                f"Verificación de {tipo}",
                f"Verifique que todos los {tipo} se encuentren conectados.\n\nPresione OK para continuar."
            )

            # Ejecutar comando con todos conectados
            self.escribir_en_archivo(f"\n=== Verificación inicial - Todos los {tipo} conectados ===\n")
            for cmd_config in config_prueba.get("comandos", []):
                comando = cmd_config.get("comando")
                espera = cmd_config.get("espera", ESPERA_COMANDO)

                self.log(f"Ejecutando: {comando} (todos conectados)", "command")
                resultado = ejecutar_comando_completo_con_prompt(conexion, comando, espera=espera)
                self.escribir_comando_resultado(resultado)

            # PASO 2: Para cada componente, desconectar -> comando -> reconectar -> comando
            for i in range(1, cantidad_repeticiones + 1):
                # Solicitar desconexión
                self.log(f"Solicitando desconexión: {nombre_componente} {i}", "warning")
                self.mostrar_popup(
                    f"⚠️ Desconectar {nombre_componente.capitalize()} {i}",
                    f"Por favor, desconecte el {nombre_componente} {i} del dispositivo.\n\n"
                    f"Una vez desconectado, presione OK para ejecutar la verificación."
                )

                self.escribir_en_archivo(f"\n=== {nombre_componente.capitalize()} {i} DESCONECTADO ===\n")

                # Ejecutar comando con el componente desconectado
                for cmd_config in config_prueba.get("comandos", []):
                    comando = cmd_config.get("comando")
                    espera = cmd_config.get("espera", ESPERA_COMANDO)

                    self.log(f"Ejecutando: {comando} ({nombre_componente} {i} desconectado)", "command")
                    resultado = ejecutar_comando_completo_con_prompt(conexion, comando, espera=espera)
                    self.escribir_comando_resultado(resultado)

                time.sleep(0.5)

                # Solicitar reconexión del componente
                self.log(f"Solicitando reconexión: {nombre_componente} {i}", "info")
                self.mostrar_popup(
                    f"✅ Reconectar {nombre_componente.capitalize()} {i}",
                    f"Por favor, vuelva a conectar el {nombre_componente} {i} al dispositivo.\n\n"
                    f"Una vez conectado, presione OK para continuar."
                )

                self.escribir_en_archivo(f"\n=== {nombre_componente.capitalize()} {i} RECONECTADO ===\n")

                # Ejecutar comando nuevamente con el componente YA reconectado
                for cmd_config in config_prueba.get("comandos", []):
                    comando = cmd_config.get("comando")
                    espera = cmd_config.get("espera", ESPERA_COMANDO)

                    self.log(f"Ejecutando: {comando} ({nombre_componente} {i} reconectado)", "command")
                    resultado = ejecutar_comando_completo_con_prompt(conexion, comando, espera=espera)
                    self.escribir_comando_resultado(resultado)

            # PASO 3: Verificación final (todos reconectados)
            self.log(f"Verificación final: Todos los {tipo} reconectados", "success")
            self.mostrar_popup(
                f"✅ Verificación Final",
                f"Todos los {tipo} han sido reconectados.\n\nPresione OK para continuar con las pruebas."
            )

        else:
            # MODO SIN DESCONEXIÓN
            # Si no se permite desconexión, solo se ejecuta el comando 1 VEZ
            self.escribir_inicio_prueba(
                numero_prueba,
                f"{descripcion} ({cantidad_repeticiones} {tipo})"
            )

            self.log(f"Ejecutando sin desconexión - Se verán todos los {tipo} en una sola ejecución", "info")
            self.escribir_en_archivo(f"\n=== Verificación de {tipo} (todos conectados) ===\n")

            for cmd_config in config_prueba.get("comandos", []):
                comando = cmd_config.get("comando")
                espera = cmd_config.get("espera", ESPERA_COMANDO)

                self.log(f"Ejecutando: {comando}", "command")
                resultado = ejecutar_comando_completo_con_prompt(conexion, comando, espera=espera)
                self.escribir_comando_resultado(resultado)

        self.escribir_fin_prueba(numero_prueba)


    def ejecutar_prueba_4(self, conexion):
        """
        Prueba 4: reload, enable, show version

        VERSIÓN ROBUSTA con manejo correcto de:
        - Confirmaciones de reload
        - Desconexión esperada durante reinicio
        - Reconexión y estabilización
        - Validación temporal de boot
        """
        self.escribir_inicio_prueba(4, "reload, enable, show version")

        self.escribir_en_archivo("\n=== INICIANDO RELOAD DEL EQUIPO ===\n")
        self.escribir_en_archivo(f"Hora de inicio reload: {datetime.now().strftime('%H:%M:%S')}\n")
        self.log("INICIANDO RELOAD DEL EQUIPO - El dispositivo se reiniciará", "warning")

        # ==============================
        # FASE 0: ASEGURAR QUE ESTAMOS EN MODO ENABLE
        # ==============================
        # CRÍTICO: El comando reload SOLO funciona en modo enable (prompt #)
        # Si estamos en modo usuario (prompt >), el switch rechaza el comando

        self.log("Verificando modo enable antes de reload...", "info")
        logger.debug("[RELOAD] Verificando que estamos en modo enable")

        # Limpiar buffer
        try:
            conexion.reset_input_buffer()
        except:
            pass

        # Obtener prompt actual
        conexion.write(b"\n")
        time.sleep(0.5)
        prompt_check = ""
        if conexion.in_waiting > 0:
            prompt_check = conexion.read(conexion.in_waiting).decode('utf-8', errors='ignore')
            self.escribir_en_archivo(prompt_check)

        logger.debug(f"[RELOAD] Prompt actual: {repr(prompt_check)}")

        # Verificar si estamos en modo enable (prompt termina en #)
        if "#" not in prompt_check:
            self.log("NO estamos en modo enable, intentando entrar...", "warning")
            logger.warning("[RELOAD] Prompt no contiene #, entrando a modo enable")

            # Intentar entrar a modo enable
            if self.password_enable:
                try:
                    entrar_modo_enable(conexion, self.password_enable)
                    self.log("Modo enable activado correctamente", "success")
                except Exception as e:
                    logger.error(f"[RELOAD] Error entrando a modo enable: {e}")
                    raise TimeoutConexionError(
                        f"No se pudo entrar a modo enable antes del reload. "
                        f"Error: {str(e)}. Las pruebas se han detenido."
                    )
            else:
                # Sin password configurado, intentar igual
                logger.warning("[RELOAD] Sin password configurado, intentando enable sin password")
                conexion.write(b"enable\n")
                time.sleep(1)

                # Verificar que funcionó
                conexion.write(b"\n")
                time.sleep(0.5)
                check_enable = ""
                if conexion.in_waiting > 0:
                    check_enable = conexion.read(conexion.in_waiting).decode('utf-8', errors='ignore')

                if "#" not in check_enable:
                    raise TimeoutConexionError(
                        "No se pudo entrar a modo enable (no hay password configurado). "
                        "Configure una contraseña de enable en la configuración de pruebas."
                    )
        else:
            self.log("Ya estamos en modo enable (#)", "success")
            logger.debug("[RELOAD] Confirmado: estamos en modo enable")

        # ==============================
        # FASE 1: ENVIAR RELOAD Y CONFIRMAR
        # ==============================
        self.log("Enviando comando: reload", "command")

        # CRÍTICO: Limpiar buffer ANTES de enviar reload para evitar confusiones
        try:
            conexion.reset_input_buffer()
            logger.debug("[RELOAD] Buffer de entrada limpiado")
        except:
            pass

        # Obtener prompt actual (ahora sabemos que es #)
        conexion.write(b"\n")
        time.sleep(0.5)
        if conexion.in_waiting > 0:
            prompt_actual = conexion.read(conexion.in_waiting).decode('utf-8', errors='ignore')
            self.escribir_en_archivo(prompt_actual)

        # Enviar comando reload (el eco lo recibiremos del switch, no lo escribimos manualmente)
        conexion.write(b"reload\n")
        time.sleep(3)  # Espera inicial para que el switch procese

        # Leer y procesar respuesta completa con timeout LARGO (45 segundos)
        # Algunos switches tardan en mostrar los prompts
        respuesta_reload_completa = ""
        confirmacion_enviada = False
        save_respondido = False

        tiempo_inicio_lectura = time.time()
        TIMEOUT_RESPUESTA_RELOAD = 45  # 45 segundos para capturar TODA la interacción

        self.log("Esperando respuesta del dispositivo (puede solicitar confirmaciones)...", "info")

        # IMPORTANTE: NO resetear el timeout cuando hay datos para evitar bucles infinitos
        # El timeout es absoluto: 45 segundos desde que se envió reload
        while time.time() - tiempo_inicio_lectura < TIMEOUT_RESPUESTA_RELOAD:
            if conexion.in_waiting > 0:
                try:
                    datos = conexion.read(conexion.in_waiting).decode('utf-8', errors='ignore')
                    respuesta_reload_completa += datos
                    self.escribir_en_archivo(datos)
                    logger.debug(f"[RELOAD] Recibido: {datos[:100]}")
                except Exception as e:
                    logger.error(f"[RELOAD] Error leyendo: {e}")
                    break

            # Analizar la respuesta acumulada para detectar prompts

            # 1. Detectar solicitud de guardar configuración
            if ("Save?" in respuesta_reload_completa or
                "System configuration has been modified" in respuesta_reload_completa) and not save_respondido:
                self.log("Detectado: 'Save configuration?' - Respondiendo 'no'", "info")
                # Enviar respuesta (el eco lo recibiremos del switch)
                conexion.write(b"no\n")
                time.sleep(1)
                save_respondido = True
                continue  # Continuar leyendo

            # 2. Detectar solicitud de confirmación de reload
            if (("Proceed with reload?" in respuesta_reload_completa or
                 "[confirm]" in respuesta_reload_completa) and not confirmacion_enviada):
                self.log("Detectado: 'Proceed with reload? [confirm]' - Confirmando...", "info")

                # MEJORA: Enviar confirmación MÚLTIPLES VECES para asegurar que llega
                # A veces el primer Enter no es procesado correctamente
                for intento_confirm in range(3):
                    logger.debug(f"[RELOAD] Enviando confirmación, intento {intento_confirm + 1}/3")
                    conexion.write(b"\n")
                    time.sleep(0.5)

                confirmacion_enviada = True
                self.log("Confirmación enviada (3 veces para asegurar recepción)", "success")
                # Continuar leyendo para capturar mensajes de shutdown
                time.sleep(2)  # Espera adicional para recibir respuesta

            # 3. Verificar que el reload realmente se está ejecutando
            # Buscar mensajes típicos de inicio de reload
            if confirmacion_enviada and any(msg in respuesta_reload_completa for msg in [
                "Reload requested", "Proceeding with reload", "***", "System Bootstrap",
                "reload in", "Reload command"  # Mensajes adicionales
            ]):
                self.log("Reload confirmado - El dispositivo está reiniciando", "success")
                # Esperar un poco más para capturar mensajes finales
                time.sleep(5)
                # Leer últimos datos
                if conexion.in_waiting > 0:
                    datos_finales = conexion.read(conexion.in_waiting).decode('utf-8', errors='ignore')
                    respuesta_reload_completa += datos_finales
                    self.escribir_en_archivo(datos_finales)
                break

            time.sleep(0.5)

        # VALIDACIÓN CRÍTICA: Verificar que se confirmó el reload
        if not confirmacion_enviada:
            logger.error("[RELOAD] NO SE DETECTÓ PROMPT DE CONFIRMACIÓN")
            logger.error(f"[RELOAD] Respuesta recibida: {repr(respuesta_reload_completa[:500])}")
            self.log("ERROR CRÍTICO: No se detectó prompt de confirmación de reload", "error")
            self.log("El comando 'reload' no fue confirmado correctamente", "error")
            self.escribir_en_archivo("\n[ERROR CRÍTICO] El reload NO fue confirmado\n")
            self.escribir_en_archivo(f"Respuesta recibida del switch:\n{respuesta_reload_completa}\n")

            # DETENER LAS PRUEBAS - No tiene sentido continuar
            raise TimeoutConexionError(
                "No se pudo confirmar el comando reload. "
                "El switch no mostró el prompt '[confirm]' esperado. "
                "Verifique manualmente si hay alguna configuración especial en el switch. "
                "Las pruebas se han detenido."
            )

        # Verificar que realmente se detectaron mensajes de shutdown
        reload_ejecutandose = any(msg in respuesta_reload_completa for msg in [
            "Reload requested", "Proceeding with reload", "***", "System Bootstrap",
            "reload in", "Reload command"
        ])

        if not reload_ejecutandose:
            logger.warning("[RELOAD] Confirmación enviada pero NO se detectaron mensajes de shutdown")
            logger.warning(f"[RELOAD] Respuesta completa: {repr(respuesta_reload_completa[:500])}")
            self.log("ADVERTENCIA: Confirmación enviada pero no se detectaron mensajes de reinicio", "warning")
            self.log("Es posible que el reload NO se haya ejecutado. Monitoreando...", "warning")
            self.escribir_en_archivo("\n[ADVERTENCIA] No se detectaron mensajes claros de inicio de reload\n")
        else:
            self.log("Confirmación de reload enviada Y mensajes de shutdown detectados", "success")

        # ==============================
        # FASE 2: ESPERA DE RELOAD CON VALIDACIÓN TEMPORAL
        # ==============================
        self.log(f"Esperando {ESPERA_RELOAD} segundos para que el equipo reinicie...", "warning")
        self.escribir_en_archivo(f"\n=== ESPERANDO {ESPERA_RELOAD} SEGUNDOS PARA REINICIO ===\n")

        # CRÍTICO: Limpiar buffer para no confundir datos viejos con mensajes de boot
        try:
            time.sleep(2)
            conexion.reset_input_buffer()
            logger.debug("[RELOAD] Buffer limpiado antes de monitorear boot")
        except:
            pass

        tiempo_inicio_reload = time.time()
        boot_detectado = False
        tiempo_boot_detectado = None
        TIEMPO_MINIMO_BOOT = 45  # Mínimo 45 segundos antes de aceptar boot

        while time.time() - tiempo_inicio_reload < ESPERA_RELOAD:
            tiempo_transcurrido = time.time() - tiempo_inicio_reload

            # Leer datos disponibles sin lanzar excepciones
            if conexion.in_waiting > 0:
                try:
                    datos_bytes = conexion.read(conexion.in_waiting)
                    datos = datos_bytes.decode('utf-8', errors='ignore')

                    if datos:
                        self.escribir_en_archivo(datos)

                        # Buscar patrones ESPECÍFICOS de boot (no solo >)
                        # IMPORTANTE: Solo si han pasado al menos 45 segundos
                        if tiempo_transcurrido >= TIEMPO_MINIMO_BOOT:
                            if any(patron in datos for patron in [
                                "Press RETURN to get started",
                                "Initial configuration dialog",
                                "Would you like to enter the initial configuration dialog?"
                            ]):
                                if not boot_detectado:
                                    self.log(f"Detectado inicio del sistema después de {int(tiempo_transcurrido)}s", "success")
                                    boot_detectado = True
                                    tiempo_boot_detectado = time.time()
                                    # NO hacer break, continuar monitoreando
                        else:
                            # Antes de 45 segundos, ignorar patrones (probablemente falsos positivos)
                            if "Press RETURN" in datos or "Switch>" in datos:
                                logger.warning(f"[RELOAD] Patrón de boot detectado a los {int(tiempo_transcurrido)}s - DEMASIADO PRONTO, ignorando")

                except Exception as e:
                    # Error leyendo (puede ser normal durante desconexión), continuar
                    logger.debug(f"[RELOAD] Error leyendo datos durante boot: {e}")
                    pass

            time.sleep(1)

        # Si se detectó boot antes del timeout, esperar 10 segundos adicionales de estabilización
        if boot_detectado and tiempo_boot_detectado:
            tiempo_desde_boot = time.time() - tiempo_boot_detectado
            if tiempo_desde_boot < 10:
                espera_adicional = 10 - tiempo_desde_boot
                self.log(f"Esperando {int(espera_adicional)}s adicionales para estabilización...", "info")
                time.sleep(espera_adicional)
        else:
            # No se detectó boot específicamente, esperar 10 segundos de todas formas
            self.log("No se detectaron mensajes de boot específicos, esperando estabilización...", "warning")
            time.sleep(10)

        # ==============================
        # FASE 3: RECONEXIÓN ROBUSTA
        # ==============================
        self.escribir_en_archivo("\n=== EQUIPO REINICIADO - RECONECTANDO ===\n")
        self.log("Equipo reiniciado - Intentando reconectar...", "info")

        # Intentar despertar la consola y obtener prompt
        conexion_exitosa = False
        MAX_INTENTOS_RECONEXION = 15

        for intento in range(MAX_INTENTOS_RECONEXION):
            self.log(f"Intento de reconexión {intento + 1}/{MAX_INTENTOS_RECONEXION}", "info")

            try:
                # Enviar múltiples Enters
                for _ in range(3):
                    conexion.write(b"\r\n")
                    time.sleep(0.5)

                # Esperar respuesta (timeout generoso)
                time.sleep(2)
                respuesta = ""

                if conexion.in_waiting > 0:
                    datos_bytes = conexion.read(conexion.in_waiting)
                    respuesta = datos_bytes.decode('utf-8', errors='ignore')

                    # Escribir en archivo solo lo que responde el switch
                    if respuesta:
                        self.escribir_en_archivo(respuesta)

                    # Buscar prompt AL FINAL de la respuesta
                    lineas = respuesta.strip().split('\n')
                    ultima_linea = lineas[-1] if lineas else ""

                    if ultima_linea.endswith('>') or ultima_linea.endswith('#'):
                        self.log(f"Consola disponible después de {intento + 1} intentos - Prompt: '{ultima_linea[-30:]}'", "success")
                        conexion_exitosa = True
                        break

            except Exception as e:
                self.log(f"Intento {intento + 1} falló: {str(e)[:50]}", "warning")
                logger.debug(f"[RECONEXION] Error en intento {intento + 1}: {e}")

            time.sleep(5)  # Espera entre intentos

        # CRÍTICO: Validar que se reconectó
        if not conexion_exitosa:
            self.log("No se pudo reconectar después de 15 intentos", "error")

            # Última verificación: ¿es problema físico o el switch no responde?
            try:
                if not verificar_conexion_activa(conexion):
                    raise DispositivoDesconectadoError(
                        "No se pudo reconectar después del reload. "
                        "La conexión física se perdió. Verifique el cable y el dispositivo."
                    )
                else:
                    raise TimeoutConexionError(
                        "No se pudo reconectar al dispositivo después de 15 intentos. "
                        "El dispositivo puede estar bloqueado o no respondiendo correctamente."
                    )
            except:
                # Si verificar_conexion_activa también falla, es desconexión física
                raise DispositivoDesconectadoError(
                    "Conexión perdida después del reload. Verifique el cable y el dispositivo."
                )

        # Estabilizar consola antes de continuar
        self.log("Estabilizando consola post-reload...", "info")
        estabilizado = estabilizar_consola_post_reload(conexion, max_intentos=10)

        if not estabilizado:
            self.log("ADVERTENCIA: Consola no completamente estabilizada, continuando de todas formas", "warning")

        # ==============================
        # VALIDACIÓN CRÍTICA: Verificar que el switch REALMENTE se reinició
        # ==============================
        self.log("Verificando que el switch realmente se reinició...", "info")
        logger.debug("[RELOAD] Verificando uptime del switch para confirmar reinicio")

        try:
            # Enviar "show version" para obtener el uptime
            conexion.write(b"\n")
            time.sleep(0.3)
            if conexion.in_waiting > 0:
                conexion.read(conexion.in_waiting)  # Limpiar

            conexion.write(b"show version | include uptime\n")
            time.sleep(2)

            respuesta_uptime = ""
            if conexion.in_waiting > 0:
                respuesta_uptime = conexion.read(conexion.in_waiting).decode('utf-8', errors='ignore')

            logger.debug(f"[RELOAD] Respuesta uptime: {repr(respuesta_uptime)}")

            # Buscar el uptime en la respuesta
            # Formato típico: "Switch uptime is 2 minutes" o "Router uptime is 5 hours, 32 minutes"
            import re
            uptime_match = re.search(r'uptime is (.+)', respuesta_uptime, re.IGNORECASE)

            if uptime_match:
                uptime_str = uptime_match.group(1).strip()
                logger.debug(f"[RELOAD] Uptime detectado: {uptime_str}")

                # Si el uptime contiene "hour" o más de 10 minutos, el reload NO se ejecutó
                if "hour" in uptime_str.lower() or "day" in uptime_str.lower() or "week" in uptime_str.lower():
                    logger.error(f"[RELOAD] UPTIME ALTO DETECTADO: {uptime_str}")
                    self.log(f"ERROR: El switch NO se reinició. Uptime actual: {uptime_str}", "error")
                    self.escribir_en_archivo(f"\n[ERROR CRÍTICO] El switch NO se reinició\n")
                    self.escribir_en_archivo(f"Uptime detectado: {uptime_str}\n")

                    raise TimeoutConexionError(
                        f"El reload NO se ejecutó correctamente. "
                        f"El switch sigue con uptime de {uptime_str}. "
                        f"Debería tener menos de 10 minutos de uptime después del reload. "
                        f"Las pruebas se han detenido. "
                        f"Por favor, ejecute 'reload' manualmente en el switch y vuelva a intentar."
                    )

                # Verificar minutos
                minute_match = re.search(r'(\d+)\s+minute', uptime_str)
                if minute_match:
                    minutos = int(minute_match.group(1))
                    if minutos > 15:
                        logger.error(f"[RELOAD] UPTIME ALTO: {minutos} minutos")
                        self.log(f"ERROR: El switch NO se reinició. Uptime: {minutos} minutos", "error")
                        self.escribir_en_archivo(f"\n[ERROR] Uptime demasiado alto: {minutos} minutos\n")

                        raise TimeoutConexionError(
                            f"El reload NO se ejecutó. El switch tiene {minutos} minutos de uptime. "
                            f"Debería tener menos de 10 minutos. Las pruebas se han detenido."
                        )

                self.log(f"Uptime verificado: {uptime_str} - Reload confirmado", "success")
                logger.info(f"[RELOAD] Reload VERIFICADO. Uptime: {uptime_str}")
            else:
                # No se pudo obtener uptime, continuar con advertencia
                self.log("ADVERTENCIA: No se pudo verificar el uptime del switch", "warning")
                logger.warning("[RELOAD] No se pudo extraer uptime de la respuesta")

        except TimeoutConexionError:
            # Re-lanzar la excepción de uptime alto
            raise
        except Exception as e:
            # Error obteniendo uptime, continuar con advertencia
            self.log(f"ADVERTENCIA: Error verificando uptime: {str(e)[:50]}", "warning")
            logger.warning(f"[RELOAD] Error verificando uptime: {e}")

        # ==============================
        # FASE 4: ENTRAR A MODO ENABLE (SIN VERIFICACIÓN ESTRICTA)
        # ==============================
        self.escribir_en_archivo("\n=== ENTRANDO A MODO ENABLE (POST RELOAD) ===\n")
        self.log("Entrando a modo enable...", "info")

        # Usar función especializada que maneja TODO el flujo de enable (con password si es necesario)
        # en una SOLA operación, capturando el CLI completo sin interrupciones
        resultado_enable_completo = entrar_modo_enable_sin_verificacion(conexion, password=self.password_enable)
        self.escribir_comando_resultado(resultado_enable_completo)

        # Verificar si se logró entrar a modo enable
        if "#" in resultado_enable_completo:
            self.log("Modo enable activado correctamente", "success")
        else:
            self.log("ADVERTENCIA: No se detectó prompt '#' después de enable", "warning")

        # ==============================
        # FASE 5: CONFIGURAR TERMINAL
        # ==============================
        self.log("Configurando terminal...", "info")
        ejecutar_comando_sin_verificacion(conexion, "terminal length 0", espera=1)
        ejecutar_comando_sin_verificacion(conexion, "terminal width 512", espera=1)

        # ==============================
        # FASE 6: SHOW VERSION POST RELOAD
        # ==============================
        time.sleep(3)  # Pausa adicional para asegurar estabilidad
        self.escribir_en_archivo("\n=== EJECUTANDO SHOW VERSION (POST RELOAD) ===\n")
        self.log("Ejecutando: show version (post reload)", "command")

        # Usar versión COMPLETA sin verificación (captura prompt + comando + respuesta)
        resultado_version = ejecutar_comando_completo_sin_verificacion(conexion, "show version", espera=3)

        # Validar que se obtuvo output real
        if len(resultado_version) > 50:  # Al menos 50 caracteres (output válido)
            self.escribir_comando_resultado(resultado_version)
            self.log(f"Show version ejecutado correctamente ({len(resultado_version)} caracteres)", "success")
        else:
            self.log(f"ADVERTENCIA: Show version retornó muy pocos datos ({len(resultado_version)} caracteres)", "warning")
            self.escribir_en_archivo("[ADVERTENCIA] Output de show version incompleto o vacío\n")
            # Intentar una vez más
            time.sleep(2)
            self.log("Reintentando show version...", "info")
            resultado_version_retry = ejecutar_comando_completo_sin_verificacion(conexion, "show version", espera=4)
            self.escribir_comando_resultado(resultado_version_retry)

        self.escribir_fin_prueba(4)

        # IMPORTANTE: Restaurar verificaciones estrictas para pruebas siguientes
        # La próxima prueba (si la hay) usará las funciones normales con verificación


    def run(self):
        """Método principal del thread que ejecuta todas las pruebas"""
        try:
            # Inicializar archivo de salida (SIN limpieza de datos - CLI exacto del dispositivo)
            self.contenido_archivo = []
            self.contenido_archivo.append("=" * 80 + "\n")
            self.contenido_archivo.append(f"RESULTADO DE PRUEBAS - {self.modelo_dispositivo.upper()}\n")
            self.contenido_archivo.append("=" * 80 + "\n")
            self.contenido_archivo.append(f"Fecha y hora de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.contenido_archivo.append("=" * 80 + "\n\n")

            # Abrir conexión serial
            self.log(f"Conectando al puerto {self.puerto} a {self.baudrate} baudios...", "info")

            try:
                conexion = abrir_conexion_serial(self.puerto, self.baudrate)
                self.log("Conexión establecida y dispositivo Cisco validado correctamente", "success")
            except ValueError as error:
                # Error de validación de inputs (puerto o baudrate inválidos)
                self.log(f"ERROR DE VALIDACIÓN: {str(error)}", "error")
                self.finished_signal.emit(False, "")
                return
            except SerialException as error:
                # Error abriendo el puerto (no existe, en uso, sin permisos)
                self.log(f"ERROR DE PUERTO SERIAL: No se pudo abrir el puerto {self.puerto}", "error")
                self.log(f"Detalles: {str(error)}", "error")
                self.log("Verifique que el puerto existe y no esté siendo usado por otra aplicación", "error")
                self.finished_signal.emit(False, "")
                return
            except DispositivoNoDetectadoError as error:
                # Puerto abre pero no hay dispositivo Cisco
                self.log(f"DISPOSITIVO NO DETECTADO: {str(error)}", "error")
                self.log("El puerto existe pero no hay un dispositivo Cisco respondiendo", "error")
                self.log("Verifique que el cable esté conectado y el dispositivo encendido", "error")
                self.finished_signal.emit(False, "")
                return
            except TimeoutConexionError as error:
                # Timeout validando dispositivo
                self.log(f"TIMEOUT DE CONEXIÓN: {str(error)}", "error")
                self.log("El dispositivo no responde. Verifique la configuración y conexión", "error")
                self.finished_signal.emit(False, "")
                return
            except Exception as error:
                # Error inesperado
                self.log(f"ERROR INESPERADO abriendo conexión: {str(error)}", "error")
                logger.exception("Error inesperado en abrir_conexion_serial")
                self.finished_signal.emit(False, "")
                return

            # Preparar la conexión
            self.log("Despertando consola...", "info")
            despertar_consola(conexion)

            if self.password_enable:
                self.log("Entrando a modo privilegiado (enable)...", "info")
                entrar_modo_enable(conexion, self.password_enable)
            else:
                self.log("Sin contraseña configurada, omitiendo modo enable", "warning")

            self.log("Configurando terminal...", "info")
            configurar_terminal(conexion)

            # PRUEBA 1
            self.log("Preparando Prueba 1...", "info")
            # CRÍTICO: Verificar conexión antes de cada prueba
            if not verificar_conexion_activa(conexion):
                raise DispositivoDesconectadoError("Conexión perdida antes de ejecutar Prueba 1")

            config_prueba1 = self.mapeo.get("prueba_1", {})
            self.ejecutar_prueba_generica(conexion, 1, config_prueba1)

            # Usar las cantidades configuradas por el usuario (sin autocalculo)
            cantidad_psu = self.num_fuentes
            cantidad_fan = self.num_ventiladores

            self.log(f"Fuentes de poder configuradas: {cantidad_psu}", "info")
            self.log(f"Ventiladores configurados: {cantidad_fan}", "info")

            # PRUEBA 2 (show environment power)
            self.log("Preparando Prueba 2...", "info")
            # CRÍTICO: Verificar conexión antes de cada prueba
            if not verificar_conexion_activa(conexion):
                raise DispositivoDesconectadoError("Conexión perdida antes de ejecutar Prueba 2")

            config_prueba2 = self.mapeo.get("prueba_2", {})
            if config_prueba2.get("repetir_por_fuentes"):
                self.ejecutar_prueba_repetitiva(
                    conexion, 2, config_prueba2, cantidad_psu,
                    tipo="fuente(s)",
                    nombre_componente="fuente de poder"
                )
            else:
                self.ejecutar_prueba_generica(conexion, 2, config_prueba2)

            # PRUEBA 3 (show environment fan)
            self.log("Preparando Prueba 3...", "info")
            # CRÍTICO: Verificar conexión antes de cada prueba
            if not verificar_conexion_activa(conexion):
                raise DispositivoDesconectadoError("Conexión perdida antes de ejecutar Prueba 3")

            config_prueba3 = self.mapeo.get("prueba_3", {})
            if config_prueba3.get("repetir_por_ventiladores"):
                self.ejecutar_prueba_repetitiva(
                    conexion, 3, config_prueba3, cantidad_fan,
                    tipo="ventilador(es)",
                    nombre_componente="ventilador"
                )
            else:
                self.ejecutar_prueba_generica(conexion, 3, config_prueba3)

            # PRUEBA 4 (reload - siempre se ejecuta)
            self.log("Preparando Prueba 4 (RELOAD)...", "info")
            # CRÍTICO: Verificar conexión antes de cada prueba
            if not verificar_conexion_activa(conexion):
                raise DispositivoDesconectadoError("Conexión perdida antes de ejecutar Prueba 4 (reload)")

            config_prueba4 = self.mapeo.get("prueba_4", {})
            if config_prueba4.get("ejecutar_reload"):
                self.log("EJECUTANDO PRUEBA 4 (RELOAD) - EL EQUIPO SE REINICIARÁ", "warning")
                self.ejecutar_prueba_4(conexion)
            else:
                self.ejecutar_prueba_generica(conexion, 4, config_prueba4)

            # PRUEBA 5 (opcional)
            if self.ejecutar_prueba5:
                self.log("Preparando Prueba 5...", "info")
                # CRÍTICO: Verificar conexión antes de cada prueba
                if not verificar_conexion_activa(conexion):
                    raise DispositivoDesconectadoError("Conexión perdida antes de ejecutar Prueba 5")

                config_prueba5 = self.mapeo.get("prueba_5", {})
                self.log("Ejecutando Prueba 5...", "info")
                self.ejecutar_prueba_generica(conexion, 5, config_prueba5)
            else:
                config_prueba5 = self.mapeo.get("prueba_5", {})
                self.log("Prueba 5 OMITIDA por configuración", "warning")
                self.escribir_inicio_prueba(5, config_prueba5.get("descripcion", "Prueba 5") + " [OMITIDO POR CONFIGURACIÓN]")
                self.escribir_en_archivo("\n*** PRUEBA 5 NO EJECUTADA ***\n")
                self.escribir_fin_prueba(5)

            # Finalizar archivo
            self.contenido_archivo.append("\n" + "=" * 80 + "\n")
            self.contenido_archivo.append(f"PRUEBAS FINALIZADAS: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.contenido_archivo.append("=" * 80 + "\n")

            # Extraer información del dispositivo para el nombre del archivo
            lines = ''.join(self.contenido_archivo).split('\n')
            modelo, serial, version = extraer_info_dispositivo_9200(lines)

            if modelo and serial:
                # Sanitizar modelo y serial para nombre de archivo seguro
                modelo_limpio = sanitizar_nombre_archivo(modelo)
                serial_limpio = sanitizar_nombre_archivo(serial)
                nombre_archivo = f"{modelo_limpio}_{serial_limpio}.txt"
            else:
                nombre_archivo = f"resultado_pruebas_cisco_9200_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            # Sanitizar el nombre completo por seguridad
            nombre_archivo = sanitizar_nombre_archivo(nombre_archivo)
            logger.info(f"Nombre de archivo generado: {nombre_archivo}")

            # Guardar archivo con manejo de errores
            try:
                with open(nombre_archivo, 'w', encoding='utf-8') as f:
                    f.writelines(self.contenido_archivo)
                logger.info(f"Archivo guardado exitosamente: {nombre_archivo}")
            except (OSError, IOError) as error:
                logger.error(f"Error guardando archivo {nombre_archivo}: {error}")
                # Intentar con nombre genérico
                nombre_archivo = f"resultado_pruebas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                self.log(f"Error guardando archivo, intentando con nombre alternativo: {nombre_archivo}", "warning")
                with open(nombre_archivo, 'w', encoding='utf-8') as f:
                    f.writelines(self.contenido_archivo)

            self.archivo_salida = nombre_archivo
            self.log(f"Resultados guardados en: {nombre_archivo}", "success")

            # Cerrar conexión
            cerrar_conexion_serial(conexion)
            self.log("Conexión serial cerrada", "info")

            self.finished_signal.emit(True, nombre_archivo)

        except KeyboardInterrupt:
            self.log("Pruebas canceladas por el usuario", "warning")
            self.escribir_en_archivo("\n*** PRUEBAS CANCELADAS POR EL USUARIO ***\n")
            if 'conexion' in locals() and conexion:
                cerrar_conexion_serial(conexion)
            self.finished_signal.emit(False, "")

        except DispositivoDesconectadoError as error:
            # Dispositivo se desconectó durante la ejecución
            self.log("=" * 60, "error")
            self.log("DISPOSITIVO DESCONECTADO DURANTE LA EJECUCIÓN", "error")
            self.log("=" * 60, "error")
            self.log(str(error), "error")
            self.log("La conexión física con el dispositivo se perdió", "error")
            self.log("Verifique el cable serial y reconecte el dispositivo", "error")
            self.escribir_en_archivo(f"\n*** DISPOSITIVO DESCONECTADO: {str(error)} ***\n")
            self.escribir_en_archivo(f"Hora del error: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if 'conexion' in locals() and conexion:
                cerrar_conexion_serial(conexion)
            self.finished_signal.emit(False, "")

        except TimeoutConexionError as error:
            # Timeout esperando respuesta
            self.log("=" * 60, "error")
            self.log("TIMEOUT: DISPOSITIVO NO RESPONDE", "error")
            self.log("=" * 60, "error")
            self.log(str(error), "error")
            self.log("El dispositivo dejó de responder a los comandos", "error")
            self.log("Posibles causas: desconexión, dispositivo bloqueado, o apagado", "error")
            self.escribir_en_archivo(f"\n*** TIMEOUT DE CONEXIÓN: {str(error)} ***\n")
            self.escribir_en_archivo(f"Hora del error: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if 'conexion' in locals() and conexion:
                cerrar_conexion_serial(conexion)
            self.finished_signal.emit(False, "")

        except SerialException as error:
            # Error de puerto serial
            self.log("=" * 60, "error")
            self.log("ERROR DE COMUNICACIÓN SERIAL", "error")
            self.log("=" * 60, "error")
            self.log(str(error), "error")
            self.log("Error en la comunicación con el puerto serial", "error")
            self.escribir_en_archivo(f"\n*** ERROR SERIAL: {str(error)} ***\n")
            self.escribir_en_archivo(f"Hora del error: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if 'conexion' in locals() and conexion:
                cerrar_conexion_serial(conexion)
            self.finished_signal.emit(False, "")

        except Exception as error:
            # Error inesperado
            self.log("=" * 60, "error")
            self.log("ERROR CRÍTICO INESPERADO", "error")
            self.log("=" * 60, "error")
            self.log(f"Tipo de error: {type(error).__name__}", "error")
            self.log(f"Detalles: {str(error)}", "error")
            self.escribir_en_archivo(f"\n*** ERROR CRÍTICO: {type(error).__name__} - {str(error)} ***\n")
            self.escribir_en_archivo(f"Hora del error: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            logger.exception("Error crítico inesperado en TestThread.run()")
            if 'conexion' in locals() and conexion:
                cerrar_conexion_serial(conexion)
            self.finished_signal.emit(False, "")


class LoginWindow(QMainWindow):
    """Ventana de inicio de sesión - Diseño Corporativo Profesional"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FAT Testing - Authentication")
        self.setMinimumSize(520, 700)
        self.resize(560, 740)
        self.email_valid = False
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        """Configurar interfaz - Diseño Enterprise"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Container principal centrado
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setContentsMargins(50, 50, 50, 50)

        # Card principal - diseño elevado
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(440)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(28)

        # Logo y Header Section
        header_section = QVBoxLayout()
        header_section.setSpacing(16)
        header_section.setAlignment(Qt.AlignCenter)

        # Logo empresarial
        logo_container = QFrame()
        logo_container.setObjectName("logoFrame")
        logo_container.setFixedSize(64, 64)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignCenter)

        logo_text = QLabel("FT")
        logo_text.setAlignment(Qt.AlignCenter)
        logo_text.setFont(QFont("Segoe UI", 22, QFont.Bold))
        logo_text.setObjectName("logoText")
        logo_layout.addWidget(logo_text)

        header_section.addWidget(logo_container, alignment=Qt.AlignCenter)

        # Título principal
        title = QLabel("FAT Testing Platform")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setObjectName("mainTitle")
        header_section.addWidget(title)

        # Subtítulo
        subtitle = QLabel("Field Acceptance Testing for Network Devices")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        header_section.addWidget(subtitle)

        card_layout.addLayout(header_section)

        # Separator
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFixedHeight(1)
        card_layout.addWidget(separator)

        # Form Section
        form_section = QVBoxLayout()
        form_section.setSpacing(20)

        # Email Field
        email_container = QVBoxLayout()
        email_container.setSpacing(10)

        email_label = QLabel("Email Address")
        email_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        email_label.setObjectName("fieldLabel")
        email_container.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setObjectName("formInput")
        self.email_input.setPlaceholderText("your.email@company.com")
        self.email_input.setFixedHeight(42)
        self.email_input.setFont(QFont("Segoe UI", 10))
        self.email_input.textChanged.connect(self.validate_email)
        # Accesibilidad: asociar label con input
        email_label.setBuddy(self.email_input)
        self.email_input.setAccessibleName("Email Address")
        self.email_input.setAccessibleDescription("Enter your email address to login")
        email_container.addWidget(self.email_input)

        # Mensaje de validación
        self.email_validation_label = QLabel("")
        self.email_validation_label.setFont(QFont("Segoe UI", 8))
        self.email_validation_label.setObjectName("validationError")
        self.email_validation_label.setVisible(False)
        self.email_validation_label.setFixedHeight(20)
        email_container.addWidget(self.email_validation_label)

        form_section.addLayout(email_container)

        # Password Field
        password_container_outer = QVBoxLayout()
        password_container_outer.setSpacing(10)

        password_label = QLabel("Password")
        password_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        password_label.setObjectName("fieldLabel")
        password_container_outer.addWidget(password_label)

        password_wrapper = QHBoxLayout()
        password_wrapper.setSpacing(10)

        self.password_input = QLineEdit()
        self.password_input.setObjectName("formInput")
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(42)
        self.password_input.setFont(QFont("Segoe UI", 10))
        self.password_input.returnPressed.connect(self.login)
        # Accesibilidad
        password_label.setBuddy(self.password_input)
        self.password_input.setAccessibleName("Password")
        self.password_input.setAccessibleDescription("Enter your password")
        password_wrapper.addWidget(self.password_input)

        # Botón toggle password - sin emoji
        self.toggle_password_btn = QPushButton("Show")
        self.toggle_password_btn.setObjectName("togglePasswordBtn")
        self.toggle_password_btn.setFixedSize(70, 42)
        self.toggle_password_btn.setFont(QFont("Segoe UI", 9))
        self.toggle_password_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)
        self.toggle_password_btn.setAccessibleName("Toggle password visibility")
        self.toggle_password_btn.setAccessibleDescription("Show or hide password")
        # Atajo de teclado Alt+S para toggle password
        self.toggle_password_btn.setShortcut("Alt+S")
        password_wrapper.addWidget(self.toggle_password_btn)

        password_container_outer.addLayout(password_wrapper)
        form_section.addLayout(password_container_outer)

        card_layout.addLayout(form_section)

        # Action Section
        action_section = QVBoxLayout()
        action_section.setSpacing(14)

        # Login button
        self.login_button = QPushButton("Sign In")
        self.login_button.setObjectName("primaryButton")
        self.login_button.setFixedHeight(46)
        self.login_button.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.login)
        # Accesibilidad y atajo de teclado
        self.login_button.setAccessibleName("Sign In")
        self.login_button.setAccessibleDescription("Click to login with your credentials")
        self.login_button.setShortcut("Alt+L")
        self.login_button.setDefault(True)  # Enter activa este botón por defecto
        action_section.addWidget(self.login_button)

        # Footer link
        footer_container = QHBoxLayout()
        footer_container.setAlignment(Qt.AlignCenter)
        footer_container.setSpacing(6)

        footer_text = QLabel("Need help?")
        footer_text.setObjectName("footerText")
        footer_text.setFont(QFont("Segoe UI", 9))
        footer_container.addWidget(footer_text)

        contact_link = QPushButton("Contact Administrator")
        contact_link.setObjectName("textLink")
        contact_link.setFlat(True)
        contact_link.setFont(QFont("Segoe UI", 9, QFont.Medium))
        contact_link.setCursor(Qt.PointingHandCursor)
        contact_link.clicked.connect(self.open_register)
        footer_container.addWidget(contact_link)

        action_section.addLayout(footer_container)

        card_layout.addLayout(action_section)

        container_layout.addWidget(card)
        main_layout.addWidget(container)

    def apply_styles(self):
        """Aplicar estilos Corporativos Profesionales"""
        self.setStyleSheet("""
            /* ========== BACKGROUND ========== */
            QMainWindow {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f1f5f9, stop:1 #e2e8f0
                );
            }

            /* ========== LOGIN CARD ========== */
            QFrame#loginCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }

            /* ========== LOGO FRAME ========== */
            QFrame#logoFrame {
                background-color: #1a56db;
                border-radius: 12px;
            }

            QLabel#logoText {
                color: #ffffff;
                font-weight: 700;
            }

            /* ========== TYPOGRAPHY ========== */
            QLabel#mainTitle {
                color: #0f172a;
                font-weight: 700;
                letter-spacing: -0.5px;
            }

            QLabel#subtitle {
                color: #64748b;
                font-weight: 400;
            }

            QLabel#fieldLabel {
                color: #334155;
                font-weight: 500;
            }

            QLabel#footerText {
                color: #64748b;
            }

            QLabel#validationError {
                color: #dc2626;
                font-weight: 500;
            }

            /* ========== SEPARATOR ========== */
            QFrame#separator {
                background-color: #e2e8f0;
            }

            /* ========== FORM INPUTS ========== */
            QLineEdit#formInput {
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 0 16px;
                background-color: #ffffff;
                color: #0f172a;
                font-size: 10pt;
                selection-background-color: #1a56db;
                selection-color: white;
            }

            QLineEdit#formInput:focus {
                border: 1.5px solid #1a56db;
                background-color: #f8fafc;
            }

            QLineEdit#formInput:hover {
                border-color: #94a3b8;
            }

            QLineEdit#formInput[valid="true"] {
                border: 1.5px solid #10b981;
            }

            QLineEdit#formInput[valid="false"] {
                border: 1.5px solid #dc2626;
            }

            /* ========== TOGGLE PASSWORD BUTTON ========== */
            QPushButton#togglePasswordBtn {
                background-color: #f8fafc;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                color: #475569;
                font-weight: 500;
            }

            QPushButton#togglePasswordBtn:hover {
                background-color: #e2e8f0;
                border-color: #94a3b8;
                color: #1e293b;
            }

            QPushButton#togglePasswordBtn:pressed {
                background-color: #cbd5e1;
            }

            /* ========== PRIMARY BUTTON ========== */
            QPushButton#primaryButton {
                background-color: #1a56db;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }

            QPushButton#primaryButton:hover {
                background-color: #1e40af;
            }

            QPushButton#primaryButton:pressed {
                background-color: #1e3a8a;
            }

            QPushButton#primaryButton:disabled {
                background-color: #cbd5e1;
                color: #94a3b8;
            }

            /* ========== TEXT LINK ========== */
            QPushButton#textLink {
                color: #1a56db;
                font-weight: 500;
                border: none;
                background: transparent;
                padding: 4px 8px;
                text-decoration: none;
            }

            QPushButton#textLink:hover {
                color: #1e40af;
                background-color: #eff6ff;
                border-radius: 4px;
            }
        """)

    def open_register(self):
        """Abrir pantalla de registro"""
        show_message(
            self,
            "Registro de Usuario",
            "Para crear una cuenta nueva, contacte al administrador del sistema.\n\n"
            "También puede registrarse en: http://localhost:5000/register",
            "info"
        )

    def validate_email(self, text):
        """Validar formato de email en tiempo real"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not text:
            self.email_validation_label.setVisible(False)
            self.email_valid = False
            self.email_input.setProperty("valid", "")
            self.email_input.style().unpolish(self.email_input)
            self.email_input.style().polish(self.email_input)
            return

        if re.match(email_pattern, text):
            self.email_validation_label.setVisible(False)
            self.email_valid = True
            self.email_input.setProperty("valid", "true")
            self.email_input.style().unpolish(self.email_input)
            self.email_input.style().polish(self.email_input)
        else:
            self.email_validation_label.setText("Invalid email format")
            self.email_validation_label.setVisible(True)
            self.email_valid = False
            self.email_input.setProperty("valid", "false")
            self.email_input.style().unpolish(self.email_input)
            self.email_input.style().polish(self.email_input)

    def toggle_password_visibility(self):
        """Alternar visibilidad de contraseña"""
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setText("Hide")
            # Actualizar descripción accesible
            self.toggle_password_btn.setAccessibleDescription("Password is visible, click to hide")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setText("Show")
            # Actualizar descripción accesible
            self.toggle_password_btn.setAccessibleDescription("Password is hidden, click to show")

    def login(self):
        """Procesar login"""
        email = self.email_input.text().strip()
        password = self.password_input.text()

        # Validación de campos obligatorios
        if not email or not password:
            show_message(self, "Campos Incompletos", "Complete todos los campos para continuar", "warning")
            return

        if not self.email_valid:
            show_message(self, "Email Inválido", "Ingrese un correo electrónico válido", "warning")
            self.email_input.setFocus()
            return

        self.login_button.setEnabled(False)
        self.login_button.setText("Authenticating...")

        try:
            with app.app_context():
                user = User.query.filter_by(email=email).first()

                # Primero validar credenciales
                if not user or not user.check_password(password):
                    show_message(self, "Authentication Failed", "Invalid email or password", "error")
                    self.login_button.setEnabled(True)
                    self.login_button.setText("Sign In")
                    self.password_input.clear()
                    self.password_input.setFocus()
                    return

                # Segundo validar estado de suscripción
                estado = (user.estado_suscripcion or "").upper()

                if estado in ESTADOS_QUE_NECESITAN_PAGO or estado != "ACTIVA":
                    # Texto más legible del estado, por si quieres mostrarlo
                    estado_legible = estado.replace("_", " ").title() if estado else "Desconocido"

                    mensaje = (
                        "Su usuario se autenticó correctamente, pero su suscripción no se encuentra activa.\n\n"
                        f"Estado actual de su suscripción: {estado_legible}.\n\n"
                        "Para utilizar el ejecutable de FAT Testing debe contar con una suscripción ACTIVA.\n"
                        "Por favor ingrese a la página oficial de FAT Testing y complete el proceso de suscripción "
                        "o reactivación de su plan. Una vez que su suscripción esté activa podrá iniciar sesión en el aplicativo de escritorio."
                    )

                    show_message(self, "Suscripción no activa", mensaje, "warning")

                    self.login_button.setEnabled(True)
                    self.login_button.setText("Sign In")
                    self.password_input.clear()
                    self.password_input.setFocus()
                    return

                # Si llegó aquí, credenciales correctas y suscripción ACTIVA
                self.main_window = MainWindow(user)
                self.main_window.show()
                self.close()

        except Exception as e:
            show_message(self, "Connection Error", f"Database connection failed:\n{str(e)}", "error")
            self.login_button.setEnabled(True)
            self.login_button.setText("Sign In")



class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""

    def __init__(self, user):
        super().__init__()
        self.user = user
        # Usar nombre si existe, sino usar email
        self.user_display_name = user.nombre if user.nombre else user.email.split('@')[0]

        self.setWindowTitle(f"FAT Testing Platform - {self.user_display_name}")
        self.setMinimumSize(1280, 860)
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        """Configurar interfaz - Diseño profesional unificado"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Navbar/Header
        navbar = self.create_navbar()
        main_layout.addWidget(navbar)

        # Panel de contenido principal
        content_panel = self.create_content_panel()
        main_layout.addWidget(content_panel)

    def create_navbar(self):
        """Crear navbar profesional con diseño limpio y funcional"""
        navbar = QFrame()
        navbar.setObjectName("navbar")
        navbar.setFixedHeight(65)

        layout = QHBoxLayout(navbar)
        layout.setContentsMargins(32, 0, 32, 0)
        layout.setSpacing(20)

        # Logo Section - Diseño limpio
        logo_section = QHBoxLayout()
        logo_section.setSpacing(12)

        # Logo badge
        logo_badge = QFrame()
        logo_badge.setObjectName("navbarLogoBadge")
        logo_badge.setFixedSize(42, 42)
        logo_badge_layout = QVBoxLayout(logo_badge)
        logo_badge_layout.setContentsMargins(0, 0, 0, 0)
        logo_badge_layout.setAlignment(Qt.AlignCenter)

        logo_badge_text = QLabel("FT")
        logo_badge_text.setAlignment(Qt.AlignCenter)
        logo_badge_text.setFont(QFont("Segoe UI", 15, QFont.Bold))
        logo_badge_text.setObjectName("navbarLogoText")
        logo_badge_layout.addWidget(logo_badge_text)

        logo_section.addWidget(logo_badge)

        # Title
        title_container = QVBoxLayout()
        title_container.setSpacing(0)
        title_container.setContentsMargins(0, 0, 0, 0)

        title = QLabel("FAT Testing")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setObjectName("navbarTitle")
        title.setContentsMargins(0, 0, 0, -10)
        title_container.addWidget(title)

        subtitle = QLabel("Factory Acceptance Testing")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setObjectName("navbarSubtitle")
        subtitle.setContentsMargins(0, -10, 0, 0)
        title_container.addWidget(subtitle)

        logo_section.addLayout(title_container)

        layout.addLayout(logo_section)
        layout.addStretch()

        # User Section
        user_section = QHBoxLayout()
        user_section.setSpacing(12)

                # User info (nombre + correo juntos)
        full_name = self.get_full_name()

        user_info = QLabel()
        user_info.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        user_info.setObjectName("navbarUserInfo")
        user_info.setText(
            f"<p style='margin:0px;'>"
            f"<span style='font-size:10pt; font-weight:600;'>{full_name}</span><br>"
            f"<span style='font-size:8pt;'>{self.user.email}</span>"
            f"</p>"
        )

        user_section.addWidget(user_info)


        # Avatar
        avatar = QFrame()
        avatar.setObjectName("navbarAvatar")
        avatar.setFixedSize(38, 38)
        avatar_layout = QVBoxLayout(avatar)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setAlignment(Qt.AlignCenter)

        initials = self.get_user_initials()
        avatar_text = QLabel(initials)
        avatar_text.setAlignment(Qt.AlignCenter)
        avatar_text.setFont(QFont("Segoe UI", 12, QFont.Bold))
        avatar_text.setObjectName("navbarAvatarText")
        avatar_layout.addWidget(avatar_text)

        user_section.addWidget(avatar)

        # Logout button
        logout_btn = QPushButton("Cerrar Sesión")
        logout_btn.setObjectName("navbarLogoutBtn")
        logout_btn.setFixedHeight(34)
        logout_btn.setMinimumWidth(100)
        logout_btn.setFont(QFont("Segoe UI", 9, QFont.Medium))
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout)
        user_section.addWidget(logout_btn)

        layout.addLayout(user_section)

        return navbar

    def get_full_name(self):
        """Obtener nombre completo del usuario"""
        if self.user.nombre and self.user.apellido:
            return f"{self.user.nombre.title()} {self.user.apellido.title()}"
        elif self.user.nombre:
            return self.user.nombre.title()
        else:
            return self.user.email.split('@')[0].title()

    def get_user_initials(self):
        """Obtener iniciales del usuario para el avatar"""
        if self.user.nombre and self.user.apellido:
            return (self.user.nombre[0] + self.user.apellido[0]).upper()
        elif self.user.nombre:
            return self.user.nombre[0].upper()
        else:
            # Usar las primeras dos letras del email
            email_name = self.user.email.split('@')[0]
            if len(email_name) >= 2:
                return email_name[:2].upper()
            return email_name[0].upper()

    def create_content_panel(self):
        """Panel de contenido principal con formulario de configuración"""
        panel = QWidget()
        panel.setObjectName("contentPanel")

        # Scroll area para el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("scrollArea")

        # Widget contenedor del scroll
        scroll_content = QWidget()
        main_layout = QVBoxLayout(scroll_content)
        main_layout.setContentsMargins(50, 30, 50, 30)
        main_layout.setSpacing(20)

        # ======================
        # FORMULARIO DE CONFIGURACIÓN
        # ======================
        form_card = QFrame()
        form_card.setObjectName("formCard")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(20)

        # Título
        title = QLabel("Configuración de Pruebas - Cisco Catalyst")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setObjectName("formTitle")
        form_layout.addWidget(title)

        # Subtítulo
        subtitle = QLabel("Complete la configuración para iniciar las pruebas del dispositivo")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setObjectName("formSubtitle")
        form_layout.addWidget(subtitle)

        # Separador
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFixedHeight(1)
        form_layout.addWidget(separator)

        # === Grupo: Selección de Dispositivo ===
        dispositivo_group = QGroupBox("Modelo de Dispositivo")
        dispositivo_group.setFont(QFont("Segoe UI", 10, QFont.Medium))
        dispositivo_layout = QVBoxLayout()
        dispositivo_layout.setSpacing(10)

        dispositivo_label = QLabel("Seleccione el modelo del dispositivo *")
        dispositivo_label.setFont(QFont("Segoe UI", 9))
        self.dispositivo_combo = QComboBox()
        self.dispositivo_combo.addItems(list(MAPEO_DISPOSITIVOS.keys()))
        self.dispositivo_combo.setFixedHeight(36)
        self.dispositivo_combo.setFont(QFont("Segoe UI", 10))
        dispositivo_layout.addWidget(dispositivo_label)
        dispositivo_layout.addWidget(self.dispositivo_combo)

        dispositivo_group.setLayout(dispositivo_layout)
        form_layout.addWidget(dispositivo_group)

        # === Grupo: Configuración de Conexión ===
        conexion_group = QGroupBox("Configuración de Conexión Serial")
        conexion_group.setFont(QFont("Segoe UI", 10, QFont.Medium))
        conexion_layout = QVBoxLayout()
        conexion_layout.setSpacing(15)

        # Puerto Serial
        puerto_layout = QVBoxLayout()
        puerto_layout.setSpacing(5)
        puerto_label = QLabel("Puerto Serial *")
        puerto_label.setFont(QFont("Segoe UI", 9))
        self.puerto_input = QLineEdit()
        self.puerto_input.setPlaceholderText("Ejemplo: COM3, COM4, /dev/ttyUSB0")
        self.puerto_input.setFixedHeight(36)
        # Accesibilidad
        puerto_label.setBuddy(self.puerto_input)
        self.puerto_input.setAccessibleName("Puerto Serial")
        self.puerto_input.setAccessibleDescription("Ingrese el puerto serial del dispositivo Cisco (ej: COM3)")
        puerto_layout.addWidget(puerto_label)
        puerto_layout.addWidget(self.puerto_input)
        conexion_layout.addLayout(puerto_layout)

        # Baudrate
        baudrate_layout = QVBoxLayout()
        baudrate_layout.setSpacing(5)
        baudrate_label = QLabel("Baudrate")
        baudrate_label.setFont(QFont("Segoe UI", 9))
        self.baudrate_input = QLineEdit("9600")
        self.baudrate_input.setPlaceholderText("Ejemplo: 9600, 115200")
        self.baudrate_input.setFixedHeight(36)
        # Accesibilidad
        baudrate_label.setBuddy(self.baudrate_input)
        self.baudrate_input.setAccessibleName("Baudrate")
        self.baudrate_input.setAccessibleDescription("Velocidad de comunicación en baudios, típicamente 9600 o 115200")
        baudrate_layout.addWidget(baudrate_label)
        baudrate_layout.addWidget(self.baudrate_input)
        conexion_layout.addLayout(baudrate_layout)

        conexion_group.setLayout(conexion_layout)
        form_layout.addWidget(conexion_group)

        # === Grupo: Credenciales (Opcional) ===
        credenciales_group = QGroupBox("Credenciales del Dispositivo (Opcional)")
        credenciales_group.setFont(QFont("Segoe UI", 10, QFont.Medium))
        credenciales_layout = QVBoxLayout()
        credenciales_layout.setSpacing(15)

        # Usuario
        usuario_layout = QVBoxLayout()
        usuario_layout.setSpacing(5)
        usuario_label = QLabel("Usuario (opcional)")
        usuario_label.setFont(QFont("Segoe UI", 9))
        self.usuario_input = QLineEdit()
        self.usuario_input.setPlaceholderText("Dejar vacío si no tiene configuración")
        self.usuario_input.setFixedHeight(36)
        usuario_layout.addWidget(usuario_label)
        usuario_layout.addWidget(self.usuario_input)
        credenciales_layout.addLayout(usuario_layout)

        # Contraseña
        password_layout = QVBoxLayout()
        password_layout.setSpacing(5)
        password_label = QLabel("Contraseña Enable (opcional)")
        password_label.setFont(QFont("Segoe UI", 9))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Dejar vacío si no tiene configuración")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(36)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        credenciales_layout.addLayout(password_layout)

        credenciales_group.setLayout(credenciales_layout)
        form_layout.addWidget(credenciales_group)

        # === Grupo: Configuración de Hardware ===
        hardware_group = QGroupBox("Configuración de Hardware")
        hardware_group.setFont(QFont("Segoe UI", 10, QFont.Medium))
        hardware_layout = QVBoxLayout()
        hardware_layout.setSpacing(15)

        info_label = QLabel("Ingrese la cantidad de componentes. Si no permite desconexión, el comando se ejecuta 1 sola vez.")
        info_label.setFont(QFont("Segoe UI", 8))
        info_label.setStyleSheet("color: #64748b; font-style: italic;")
        hardware_layout.addWidget(info_label)

        # Ventiladores
        ventiladores_layout = QHBoxLayout()
        ventiladores_label = QLabel("Número de Ventiladores:")
        ventiladores_label.setFont(QFont("Segoe UI", 9))
        self.ventiladores_input = QSpinBox()
        self.ventiladores_input.setMinimum(0)
        self.ventiladores_input.setMaximum(10)
        self.ventiladores_input.setValue(0)
        self.ventiladores_input.setFixedWidth(100)
        self.ventiladores_input.setFixedHeight(36)
        ventiladores_layout.addWidget(ventiladores_label)
        ventiladores_layout.addWidget(self.ventiladores_input)
        ventiladores_layout.addStretch()
        hardware_layout.addLayout(ventiladores_layout)

        # Fuentes de Poder
        fuentes_layout = QHBoxLayout()
        fuentes_label = QLabel("Número de Fuentes de Poder:")
        fuentes_label.setFont(QFont("Segoe UI", 9))
        self.fuentes_input = QSpinBox()
        self.fuentes_input.setMinimum(0)
        self.fuentes_input.setMaximum(10)
        self.fuentes_input.setValue(0)
        self.fuentes_input.setFixedWidth(100)
        self.fuentes_input.setFixedHeight(36)
        fuentes_layout.addWidget(fuentes_label)
        fuentes_layout.addWidget(self.fuentes_input)
        fuentes_layout.addStretch()
        hardware_layout.addLayout(fuentes_layout)

        hardware_group.setLayout(hardware_layout)
        form_layout.addWidget(hardware_group)

        # === Checkbox: Ejecutar Prueba 5 ===
        self.prueba5_checkbox = QCheckBox("Ejecutar Prueba 5 (show inventory all, show interfaces)")
        self.prueba5_checkbox.setFont(QFont("Segoe UI", 9))
        self.prueba5_checkbox.setChecked(True)
        form_layout.addWidget(self.prueba5_checkbox)

        # === Checkbox: Permitir Desconexión de Hardware ===
        self.permitir_desconexion_checkbox = QCheckBox("Permitir desconexión de ventiladores y fuentes de poder para pruebas")
        self.permitir_desconexion_checkbox.setFont(QFont("Segoe UI", 9))
        self.permitir_desconexion_checkbox.setChecked(False)
        form_layout.addWidget(self.permitir_desconexion_checkbox)

        # Nota sobre desconexión
        nota_desconexion = QLabel("(Si se marca, se solicitará desconectar y reconectar cada ventilador/fuente para verificar detección)")
        nota_desconexion.setFont(QFont("Segoe UI", 8))
        nota_desconexion.setStyleSheet("color: #64748b; font-style: italic;")
        form_layout.addWidget(nota_desconexion)

        # === Botón de Iniciar Pruebas ===
        self.start_button = QPushButton("Iniciar Pruebas")
        self.start_button.setObjectName("startButton")
        self.start_button.setFixedHeight(46)
        self.start_button.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.clicked.connect(self.iniciar_pruebas)
        # Accesibilidad y atajo de teclado
        self.start_button.setAccessibleName("Iniciar Pruebas")
        self.start_button.setAccessibleDescription("Inicia la ejecución de las pruebas en el dispositivo Cisco")
        self.start_button.setShortcut("Alt+I")
        self.start_button.setToolTip("Iniciar pruebas en el dispositivo (Alt+I)")
        form_layout.addWidget(self.start_button)

        main_layout.addWidget(form_card)

        # ======================
        # AREA DE SALIDA/LOGS
        # ======================
        output_card = QFrame()
        output_card.setObjectName("outputCard")
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(30, 30, 30, 30)
        output_layout.setSpacing(15)

        output_title = QLabel("Registro de Actividad")
        output_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        output_title.setObjectName("outputTitle")
        output_layout.addWidget(output_title)

        self.output_text = QTextEdit()
        self.output_text.setObjectName("outputText")
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(400)
        self.output_text.setFont(QFont("Cascadia Code", 9))
        output_layout.addWidget(self.output_text)

        # Botón para guardar logs
        save_button = QPushButton("Guardar Resultados")
        save_button.setObjectName("saveButton")
        save_button.setFixedHeight(40)
        save_button.setFont(QFont("Segoe UI", 10, QFont.Medium))
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.clicked.connect(self.guardar_resultados)
        output_layout.addWidget(save_button)

        main_layout.addWidget(output_card)

        scroll.setWidget(scroll_content)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(scroll)

        return panel

    def log_message(self, message, tipo="info"):
        """Agrega un mensaje al área de salida con timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        color_map = {
            "info": "#e2e8f0",
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "command": "#8b5cf6"  # Morado/violeta para mejor visibilidad
        }
        color = color_map.get(tipo, "#e2e8f0")

        formatted_message = f'<span style="color: #64748b;">[{timestamp}]</span> <span style="color: {color};">{message}</span><br>'
        self.output_text.append(formatted_message)
        self.output_text.moveCursor(QTextCursor.End)

    def iniciar_pruebas(self):
        """Inicia el proceso de pruebas"""
        # Validar campos obligatorios
        puerto = self.puerto_input.text().strip()
        if not puerto:
            show_message(self, "Campo Requerido", "Debe ingresar el puerto serial", "warning")
            self.puerto_input.setFocus()
            return

        # Validar formato del puerto
        if not validar_puerto_serial(puerto):
            show_message(
                self,
                "Puerto Inválido",
                f"El formato del puerto '{puerto}' no es válido.\n\n"
                f"Use formato COM1-99 (Windows) o /dev/ttyUSB0-99 (Linux)\n"
                f"Ejemplos: COM3, COM10, /dev/ttyUSB0",
                "warning"
            )
            self.puerto_input.setFocus()
            self.puerto_input.selectAll()
            return

        # Validar baudrate
        try:
            baudrate = int(self.baudrate_input.text().strip())
        except ValueError:
            show_message(
                self,
                "Error de Validación",
                "El baudrate debe ser un número válido",
                "warning"
            )
            self.baudrate_input.setFocus()
            self.baudrate_input.selectAll()
            return

        # Validar que el baudrate esté en la lista de valores permitidos
        if not validar_baudrate(baudrate):
            show_message(
                self,
                "Baudrate Inválido",
                f"El baudrate {baudrate} no es válido.\n\n"
                f"Valores permitidos: {', '.join(map(str, VALID_BAUDRATES))}\n\n"
                f"Los más comunes para Cisco son: 9600, 115200",
                "warning"
            )
            self.baudrate_input.setFocus()
            self.baudrate_input.selectAll()
            return

        # Obtener configuración
        modelo_dispositivo = self.dispositivo_combo.currentText()
        password_enable = self.password_input.text().strip() if self.password_input.text().strip() else ""
        num_ventiladores = self.ventiladores_input.value() if self.ventiladores_input.value() > 0 else 1
        num_fuentes = self.fuentes_input.value() if self.fuentes_input.value() > 0 else 1
        ejecutar_prueba5 = self.prueba5_checkbox.isChecked()
        permitir_desconexion = self.permitir_desconexion_checkbox.isChecked()

        # Deshabilitar el botón
        self.start_button.setEnabled(False)
        self.start_button.setText("Ejecutando Pruebas...")
        # Actualizar descripción accesible para notificar cambio de estado
        self.start_button.setAccessibleDescription("Las pruebas están en ejecución, por favor espere")

        # Limpiar el área de salida
        self.output_text.clear()

        self.log_message("=" * 60, "info")
        self.log_message(f"INICIANDO PRUEBAS - {modelo_dispositivo.upper()}", "success")
        self.log_message("=" * 60, "info")
        self.log_message(f"Modelo: {modelo_dispositivo}", "info")
        self.log_message(f"Puerto: {puerto}", "info")
        self.log_message(f"Baudrate: {baudrate}", "info")
        self.log_message(f"Ventiladores: {num_ventiladores}", "info")
        self.log_message(f"Fuentes de Poder: {num_fuentes}", "info")
        self.log_message(f"Permitir Desconexión: {'Sí' if permitir_desconexion else 'No'}", "info")
        self.log_message("Ejecutar Prueba 4 (Reload): Sí (siempre)", "info")
        self.log_message(f"Ejecutar Prueba 5: {'Sí' if ejecutar_prueba5 else 'No'}", "info")
        self.log_message("=" * 60, "info")

        # Crear y ejecutar el thread de pruebas
        self.test_thread = TestThread(
            puerto, baudrate, password_enable, num_ventiladores,
            num_fuentes, ejecutar_prueba5, modelo_dispositivo, permitir_desconexion, self
        )
        self.test_thread.log_signal.connect(self.log_message)
        self.test_thread.finished_signal.connect(self.pruebas_finalizadas)
        self.test_thread.start()

    def pruebas_finalizadas(self, success, archivo_salida=""):
        """Callback cuando las pruebas finalizan"""
        self.start_button.setEnabled(True)
        self.start_button.setText("Iniciar Pruebas")
        # Restaurar descripción accesible
        self.start_button.setAccessibleDescription("Inicia la ejecución de las pruebas en el dispositivo Cisco")

        if success:
            self.log_message("=" * 60, "info")
            self.log_message("PRUEBAS COMPLETADAS EXITOSAMENTE", "success")
            self.log_message(f"Archivo guardado: {archivo_salida}", "success")
            self.log_message("=" * 60, "info")
            show_message(self, "Pruebas Completadas", f"Las pruebas finalizaron exitosamente.\n\nArchivo: {archivo_salida}", "success")
        else:
            self.log_message("=" * 60, "info")
            self.log_message("PRUEBAS FINALIZADAS CON ERRORES", "error")
            self.log_message("=" * 60, "info")
            show_message(self, "Error en Pruebas", "Las pruebas finalizaron con errores. Revise el registro de actividad.", "error")

    def guardar_resultados(self):
        """Guarda el contenido del área de salida en un archivo"""
        if not self.output_text.toPlainText().strip():
            show_message(self, "Sin Contenido", "No hay contenido para guardar", "warning")
            return

        # Abrir diálogo para guardar archivo
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Registro de Actividad",
            f"registro_pruebas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Archivos de Texto (*.txt);;Todos los Archivos (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.output_text.toPlainText())
                show_message(self, "Guardado Exitoso", f"Registro guardado en:\n{file_path}", "success")
            except Exception as e:
                show_message(self, "Error al Guardar", f"No se pudo guardar el archivo:\n{str(e)}", "error")

    def logout(self):
        """Cerrar sesión y volver al login"""
        reply = show_message(
            self,
            "Cerrar Sesión",
            f"¿Estás seguro que deseas cerrar sesión, {self.user_display_name.title()}?",
            "warning"
        )

        # Si el usuario confirma, cerrar ventana y mostrar login
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

    def apply_styles(self):
        """Aplicar estilos modernos y limpios"""
        self.setStyleSheet("""
            /* ========== GLOBAL STYLES ========== */
            QMainWindow {
                background-color: #f8fafc;
            }

            /* ========== NAVBAR - Diseño Limpio ========== */
            QFrame#navbar {
                background-color: #1e40af;
                border: none;
            }

            /* Logo Badge */
            QFrame#navbarLogoBadge {
                background-color: #ffffff;
                border: none;
                border-radius: 10px;
            }

            QLabel#navbarLogoText {
                color: #1e40af;
                letter-spacing: 1px;
            }

            /* Títulos */
            QLabel#navbarTitle {
                color: #ffffff;
                letter-spacing: 0.5px;
            }

            QLabel#navbarSubtitle {
                color: rgba(255, 255, 255, 0.8);
                letter-spacing: 0.3px;
            }

            /* User Info Section */
            QLabel#navbarUserInfo {
                color: #ffffff;
                letter-spacing: 0.2px;
            }

            /* Avatar */
            QFrame#navbarAvatar {
                background-color: #60a5fa;
                border: none;
                border-radius: 19px;
            }

            QLabel#navbarAvatarText {
                color: #ffffff;
                letter-spacing: 1px;
            }

            /* Logout Button */
            QPushButton#navbarLogoutBtn {
                background-color: rgba(255, 255, 255, 0.12);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                letter-spacing: 0.3px;
            }

            QPushButton#navbarLogoutBtn:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }

            QPushButton#navbarLogoutBtn:pressed {
                background-color: rgba(255, 255, 255, 0.08);
            }

            /* ========== CONTENT PANEL ========== */
            QWidget#contentPanel {
                background-color: #f8fafc;
            }

            QScrollArea#scrollArea {
                border: none;
                background-color: #f8fafc;
            }

            /* ========== FORM CARD ========== */
            QFrame#formCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }

            QLabel#formTitle {
                color: #0f172a;
            }

            QLabel#formSubtitle {
                color: #64748b;
            }

            QFrame#separator {
                background-color: #e2e8f0;
            }

            /* ========== GROUP BOXES ========== */
            QGroupBox {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: 600;
                color: #1e293b;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #1e293b;
            }

            /* ========== INPUT FIELDS ========== */
            QLineEdit {
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                padding: 0 12px;
                background-color: #ffffff;
                color: #0f172a;
                selection-background-color: #1a56db;
                selection-color: white;
            }

            QLineEdit:focus {
                border: 1.5px solid #1a56db;
                background-color: #f8fafc;
            }

            QLineEdit:hover {
                border-color: #94a3b8;
            }

            /* ========== COMBOBOX ========== */
            QComboBox {
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                padding: 0 12px;
                background-color: #ffffff;
                color: #0f172a;
                selection-background-color: #1a56db;
            }

            QComboBox:focus {
                border: 1.5px solid #1a56db;
                background-color: #f8fafc;
            }

            QComboBox:hover {
                border-color: #94a3b8;
            }

            QComboBox::drop-down {
                border: none;
                width: 30px;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #64748b;
                width: 0;
                height: 0;
            }

            QComboBox QAbstractItemView {
                border: 1px solid #cbd5e1;
                background-color: #ffffff;
                selection-background-color: #1a56db;
                selection-color: white;
                padding: 4px;
            }

            /* ========== SPINBOX ========== */
            QSpinBox {
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                padding: 0 12px;
                background-color: #ffffff;
                color: #0f172a;
            }

            QSpinBox:focus {
                border: 1.5px solid #1a56db;
                background-color: #f8fafc;
            }

            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #f1f5f9;
                border: none;
                width: 20px;
            }

            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #e2e8f0;
            }

            QSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 6px solid #64748b;
                width: 0;
                height: 0;
            }

            QSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #64748b;
                width: 0;
                height: 0;
            }

            /* ========== CHECKBOX ========== */
            QCheckBox {
                color: #334155;
                spacing: 8px;
            }

            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #cbd5e1;
                border-radius: 4px;
                background-color: #ffffff;
            }

            QCheckBox::indicator:hover {
                border-color: #1a56db;
            }

            QCheckBox::indicator:checked {
                background-color: #1a56db;
                border-color: #1a56db;
            }

            QCheckBox::indicator:checked {
                image: none;
            }

            /* ========== BUTTONS ========== */
            QPushButton#startButton {
                background-color: #1a56db;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }

            QPushButton#startButton:hover {
                background-color: #1e40af;
            }

            QPushButton#startButton:pressed {
                background-color: #1e3a8a;
            }

            QPushButton#startButton:disabled {
                background-color: #cbd5e1;
                color: #94a3b8;
            }

            QPushButton#saveButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 500;
            }

            QPushButton#saveButton:hover {
                background-color: #059669;
            }

            QPushButton#saveButton:pressed {
                background-color: #047857;
            }

            /* ========== OUTPUT CARD ========== */
            QFrame#outputCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }

            QLabel#outputTitle {
                color: #0f172a;
            }

            QTextEdit#outputText {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background-color: #0f172a;
                color: #e2e8f0;
                padding: 12px;
                selection-background-color: #1a56db;
            }
        """)


def main():
    """Función principal"""
    app_qt = QApplication(sys.argv)
    app_qt.setFont(QFont("Inter", 10))

    window = LoginWindow()
    window.show()

    sys.exit(app_qt.exec())


if __name__ == '__main__':
    main()
