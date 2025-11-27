import sys
import os
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QMessageBox, QFrame, QTextEdit,
                               QSpinBox, QCheckBox, QScrollArea, QGroupBox, QComboBox, QFileDialog)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor

# Importar módulos para conexión serial
import serial
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
TIMEOUT_LECTURA = 2  # segundos
ESPERA_COMANDO = 1
ESPERA_RELOAD = 120  # 2 minutos para el reload (reducido de 3 minutos)


def abrir_conexion_serial(puerto, baudrate):
    """Abre una conexión serial con el dispositivo Cisco"""
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
        return conexion
    except serial.SerialException as error:
        return None


def cerrar_conexion_serial(conexion):
    """Cierra la conexión serial de forma segura"""
    if conexion and conexion.is_open:
        conexion.close()
        
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

def leer_respuesta_completa(conexion, timeout_total=10):
    """Lee la respuesta completa del dispositivo hasta que no haya más datos"""
    respuesta_completa = ""
    tiempo_inicio = time.time()

    while True:
        if time.time() - tiempo_inicio > timeout_total:
            break

        if conexion.in_waiting > 0:
            datos = conexion.read(conexion.in_waiting)
            try:
                texto = datos.decode("ascii", errors="ignore")
            except:
                texto = datos.decode("latin-1", errors="ignore")

            # LIMPIAR caracteres de control no imprimibles
            texto = limpiar_caracteres_control(texto)

            respuesta_completa += texto
            tiempo_inicio = time.time()
        else:
            time.sleep(0.1)

            if conexion.in_waiting == 0:
                time.sleep(0.5)
                if conexion.in_waiting == 0:
                    break

    return respuesta_completa



def enviar_comando(conexion, comando, espera=ESPERA_COMANDO):
    """Envía un comando al dispositivo y espera la respuesta"""
    conexion.reset_input_buffer()
    comando_bytes = (comando + "\n").encode('ascii')
    conexion.write(comando_bytes)
    time.sleep(espera)
    respuesta = leer_respuesta_completa(conexion)
    return respuesta


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
        """Prueba 4: reload, enable, show version"""
        self.escribir_inicio_prueba(4, "reload, enable, show version")

        self.escribir_en_archivo("\n=== INICIANDO RELOAD DEL EQUIPO ===\n")
        self.escribir_en_archivo(f"Hora de inicio reload: {datetime.now().strftime('%H:%M:%S')}\n")
        self.log("INICIANDO RELOAD DEL EQUIPO  El dispositivo se reiniciará", "warning")

        # ==============================
        # Paso 0  ejecutar reload capturando CLI completo
        # ==============================
        self.log("Enviando comando  reload", "command")

        # Esto captura
        #   prompt anterior
        #   eco del comando reload
        #   mensaje "Save? [yes/no]" si aparece
        resultado_reload = ejecutar_comando_completo_con_prompt(conexion, "reload", espera=2)

        # Escribir en el archivo exactamente lo que devolvió el CLI
        self.escribir_comando_resultado(resultado_reload)

        # Usaremos este acumulador para detectar Save y confirm
        texto_reload_total = resultado_reload

        # ==============================
        # Paso 0 1  responder a "Save? [yes/no]"
        # ==============================
        if "Save?" in texto_reload_total or "save" in texto_reload_total.lower():
            self.log("Respondiendo a Save  -> no", "info")

            # enviar_comando escribe "no" y captura la respuesta del equipo
            respuesta_save = enviar_comando(conexion, "no", espera=2)

            # De nuevo se escribe el CLI tal cual
            self.escribir_comando_resultado(respuesta_save)
            texto_reload_total += respuesta_save

        # ==============================
        # Paso 0 2  responder a "Proceed with reload? [confirm]"
        # ==============================
        if "confirm" in texto_reload_total.lower() or "proceed" in texto_reload_total.lower():
            self.log("Confirmando reload...", "info")

            # Aquí solo se envía Enter
            conexion.write(b"\n")
            time.sleep(2)
            respuesta_confirm = leer_respuesta_completa(conexion, timeout_total=5)

            # Guardar la respuesta del equipo
            self.escribir_comando_resultado(respuesta_confirm)
            texto_reload_total += respuesta_confirm

        # A partir de aquí el equipo ya está en proceso de reinicio
        self.log(f"Esperando {ESPERA_RELOAD} segundos para que el equipo reinicie...", "warning")
        self.escribir_en_archivo(f"\nEsperando {ESPERA_RELOAD} segundos para reinicio...\n")

        # Monitorear el proceso de arranque
        tiempo_inicio_reload = time.time()
        while time.time() - tiempo_inicio_reload < ESPERA_RELOAD:
            if conexion.in_waiting > 0:
                datos = leer_respuesta_completa(conexion, timeout_total=2)
                if datos:
                    self.escribir_en_archivo(datos)
                    # Detectar si el equipo ya arrancó
                    if "Press RETURN to get started" in datos or "Router>" in datos or "Switch>" in datos:
                        self.log("Detectado inicio del sistema", "success")
                        break
            time.sleep(5)

        # Esperar un poco más después de detectar el arranque
        time.sleep(10)

        self.escribir_en_archivo("\n=== EQUIPO REINICIADO  RECONECTANDO ===\n")
        self.log("Equipo reiniciado  intentando reconectar...", "info")

        # Intentar despertar la consola
        for intento in range(15):
            # Log SOLO en la UI
            self.log(f"Intento de reconexión {intento + 1}/15", "info")

            # Enviar varios Enter
            for _ in range(3):
                conexion.write(b"\r\n")
                time.sleep(0.5)

            respuesta = leer_respuesta_completa(conexion, timeout_total=3)

            # En el archivo NO escribimos "Intento X", solo lo que responde el switch
            if respuesta:
                self.escribir_en_archivo(respuesta)

            if ">" in respuesta or "#" in respuesta:
                self.log(f"Consola disponible después de {intento + 1} intentos", "success")
                break

            time.sleep(5)


        # ==============================
        # Paso 1  ENTRAR A MODO ENABLE
        # ==============================
        self.escribir_en_archivo("\n=== ENTRANDO A MODO ENABLE (POST RELOAD) ===\n")
        self.log("Entrando a modo enable...", "info")

        resultado_enable = ejecutar_comando_completo_con_prompt(conexion, "enable", espera=2)
        self.escribir_comando_resultado(resultado_enable)

        if self.password_enable and ("Password:" in resultado_enable or "password:" in resultado_enable.lower()):
            self.log("Se requiere contraseña de enable, enviando credenciales...", "info")
            respuesta_pwd = enviar_comando(conexion, self.password_enable, espera=2)
            self.escribir_comando_resultado(respuesta_pwd)

        # ==============================
        # Paso 2  CONFIGURAR TERMINAL
        # ==============================
        self.log("Configurando terminal...", "info")
        configurar_terminal(conexion)

        # ==============================
        # Paso 3  SHOW VERSION POST RELOAD
        # ==============================
        self.escribir_en_archivo("\n=== EJECUTANDO SHOW VERSION (POST RELOAD) ===\n")
        self.log("Ejecutando  show version (post reload)", "command")
        resultado_version = ejecutar_comando_completo_con_prompt(conexion, "show version", espera=3)
        self.escribir_comando_resultado(resultado_version)

        self.escribir_fin_prueba(4)


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
            conexion = abrir_conexion_serial(self.puerto, self.baudrate)

            if not conexion:
                self.log("No se pudo establecer conexión serial. Verifique el puerto y que no esté en uso.", "error")
                self.finished_signal.emit(False, "")
                return

            self.log("Conexión establecida correctamente", "success")

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
            config_prueba1 = self.mapeo.get("prueba_1", {})
            self.ejecutar_prueba_generica(conexion, 1, config_prueba1)

            # Usar las cantidades configuradas por el usuario (sin autocalculo)
            cantidad_psu = self.num_fuentes
            cantidad_fan = self.num_ventiladores

            self.log(f"Fuentes de poder configuradas: {cantidad_psu}", "info")
            self.log(f"Ventiladores configurados: {cantidad_fan}", "info")

            # PRUEBA 2 (show environment power)
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
            config_prueba4 = self.mapeo.get("prueba_4", {})
            if config_prueba4.get("ejecutar_reload"):
                self.log("EJECUTANDO PRUEBA 4 (RELOAD) - EL EQUIPO SE REINICIARÁ", "warning")
                self.ejecutar_prueba_4(conexion)
            else:
                self.ejecutar_prueba_generica(conexion, 4, config_prueba4)

            # PRUEBA 5 (opcional)
            config_prueba5 = self.mapeo.get("prueba_5", {})
            if self.ejecutar_prueba5:
                self.log("Ejecutando Prueba 5...", "info")
                self.ejecutar_prueba_generica(conexion, 5, config_prueba5)
            else:
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
                nombre_archivo = f"{modelo}_{serial}.txt"
            else:
                nombre_archivo = f"resultado_pruebas_cisco_9200_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            # Guardar archivo
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
            if conexion:
                cerrar_conexion_serial(conexion)
            self.finished_signal.emit(False, "")

        except Exception as error:
            self.log(f"ERROR CRÍTICO: {str(error)}", "error")
            self.escribir_en_archivo(f"\n*** ERROR CRÍTICO: {str(error)} ***\n")
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
        password_wrapper.addWidget(self.password_input)

        # Botón toggle password - sin emoji
        self.toggle_password_btn = QPushButton("Show")
        self.toggle_password_btn.setObjectName("togglePasswordBtn")
        self.toggle_password_btn.setFixedSize(70, 42)
        self.toggle_password_btn.setFont(QFont("Segoe UI", 9))
        self.toggle_password_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)
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
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setText("Show")

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
            return

        try:
            baudrate = int(self.baudrate_input.text().strip())
        except ValueError:
            show_message(self, "Error de Validación", "El baudrate debe ser un número válido", "warning")
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
