"""
Conector para dispositivos Cisco vía puerto serial (cable consola)
"""

import serial
import serial.tools.list_ports
import time
import re


class SerialConnector:
    """Manejador de conexión serial a dispositivos Cisco"""

    def __init__(self, port=None, baudrate=9600, timeout=1):
        """
        Inicializar conector serial

        Args:
            port: Puerto COM (ej: 'COM3')
            baudrate: Velocidad (default: 9600 para Cisco)
            timeout: Timeout en segundos
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = None
        self.is_connected = False

    @staticmethod
    def list_available_ports():
        """Lista todos los puertos COM disponibles"""
        ports = serial.tools.list_ports.comports()
        available_ports = []

        for port in ports:
            available_ports.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid
            })

        return available_ports

    def connect(self):
        """Conectar al puerto serial"""
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=self.timeout
            )

            time.sleep(0.5)  # Esperar estabilización
            self.is_connected = True
            return True, "Conexión establecida exitosamente"

        except serial.SerialException as e:
            self.is_connected = False
            return False, f"Error al conectar: {str(e)}"
        except Exception as e:
            self.is_connected = False
            return False, f"Error inesperado: {str(e)}"

    def disconnect(self):
        """Desconectar del puerto serial"""
        if self.connection and self.connection.is_open:
            self.connection.close()
            self.is_connected = False
            return True, "Desconectado exitosamente"
        return False, "No hay conexión activa"

    def send_command(self, command, wait_time=2):
        """
        Enviar comando al dispositivo

        Args:
            command: Comando a enviar
            wait_time: Tiempo de espera para respuesta (segundos)

        Returns:
            tuple: (success, output)
        """
        if not self.is_connected or not self.connection:
            return False, "No hay conexión establecida"

        try:
            # Limpiar buffer de entrada
            self.connection.reset_input_buffer()

            # Enviar comando con salto de línea
            command_bytes = f"{command}\r\n".encode('utf-8')
            self.connection.write(command_bytes)

            # Esperar respuesta
            time.sleep(wait_time)

            # Leer respuesta
            output = ""
            while self.connection.in_waiting > 0:
                chunk = self.connection.read(self.connection.in_waiting)
                output += chunk.decode('utf-8', errors='ignore')
                time.sleep(0.1)

            return True, output

        except Exception as e:
            return False, f"Error al enviar comando: {str(e)}"

    def send_special_command(self, command, confirmation="yes", wait_time=5):
        """
        Enviar comando que requiere confirmación (ej: reload)

        Args:
            command: Comando a enviar
            confirmation: Texto de confirmación (default: 'yes')
            wait_time: Tiempo de espera

        Returns:
            tuple: (success, output)
        """
        if not self.is_connected or not self.connection:
            return False, "No hay conexión establecida"

        try:
            # Enviar comando inicial
            command_bytes = f"{command}\r\n".encode('utf-8')
            self.connection.write(command_bytes)

            time.sleep(2)

            # Leer prompt de confirmación
            prompt = ""
            while self.connection.in_waiting > 0:
                chunk = self.connection.read(self.connection.in_waiting)
                prompt += chunk.decode('utf-8', errors='ignore')
                time.sleep(0.1)

            # Enviar confirmación
            if confirmation:
                confirm_bytes = f"{confirmation}\r\n".encode('utf-8')
                self.connection.write(confirm_bytes)

            time.sleep(wait_time)

            # Leer respuesta final
            output = prompt
            while self.connection.in_waiting > 0:
                chunk = self.connection.read(self.connection.in_waiting)
                output += chunk.decode('utf-8', errors='ignore')
                time.sleep(0.1)

            return True, output

        except Exception as e:
            return False, f"Error: {str(e)}"


class CiscoDeviceSimulator:
    """
    Simulador de dispositivo Cisco para pruebas sin hardware real
    """

    def __init__(self, device_model="Cisco 9300"):
        self.device_model = device_model
        self.is_connected = False
        self.power_supplies = {
            'PSU1': 'OK',
            'PSU2': 'OK'
        }
        self.psu_disconnection_count = 0

    def connect(self):
        """Simular conexión"""
        time.sleep(0.5)
        self.is_connected = True
        return True, f"[SIMULADOR] Conectado a {self.device_model}"

    def disconnect(self):
        """Simular desconexión"""
        self.is_connected = False
        return True, "[SIMULADOR] Desconectado"

    def send_command(self, command, wait_time=2):
        """Simular envío de comando"""
        time.sleep(wait_time * 0.3)  # Simular delay reducido

        # Generar respuesta según comando
        if "show version" in command.lower():
            return True, self._generate_show_version()
        elif "show inventory all" in command.lower() or "show inventory" in command.lower():
            return True, self._generate_show_inventory()
        elif "show environment power" in command.lower():
            return True, self._generate_show_environment_power()
        elif "show environment fan" in command.lower():
            return True, self._generate_show_environment_fan()
        elif "show environment status" in command.lower():
            return True, self._generate_show_environment_status()
        elif "enable" in command.lower():
            return True, f"{self.device_model}#"
        elif "show interface ethernet" in command.lower():
            return True, self._generate_show_interfaces()
        elif "reload" in command.lower():
            return True, "[SIMULADOR] Dispositivo reiniciándose... (simulado)"
        else:
            return True, f"{self.device_model}# {command}\n% Unknown command"

    def send_special_command(self, command, confirmation="yes", wait_time=5):
        """Simular comando especial"""
        return self.send_command(command, wait_time)

    def _generate_show_version(self):
        """Generar salida de show version"""
        return f"""
{self.device_model} Switch
Cisco IOS Software, {self.device_model} Software (CAT9K_IOSXE), Version 17.9.3
Copyright (c) 1986-2023 by Cisco Systems, Inc.
Compiled Wed 26-Apr-23 00:00 by prod_rel_team

System image file is "flash:packages.conf"
Last reload reason: Reload Command

{self.device_model} uptime is 2 weeks, 3 days, 5 hours, 12 minutes
System returned to ROM by reload
System image file is "bootflash:packages.conf"

Processor board ID FCW2345G0XY
1 Virtual Ethernet interface
56 Gigabit Ethernet interfaces
2048K bytes of non-volatile configuration memory.
16777216K bytes of physical memory.
1638400K bytes of Crash Files at crashinfo:.
11264000K bytes of Flash at flash:.

Configuration register is 0x102
"""

    def _generate_show_inventory(self):
        """Generar salida de show inventory"""
        return f"""
NAME: "{self.device_model} 48-Port Switch", DESCR: "{self.device_model} 48-Port Switch"
PID: C9300-48P         , VID: V01  , SN: FCW2345G0XY

NAME: "StackPort1/1", DESCR: "StackPort1/1"
PID: STACK-T1-50CM     , VID: V01  , SN: LCC2346A1BC

NAME: "Power Supply Module 1", DESCR: "800W AC Config 1 Power Supply"
PID: PWR-C1-840WA      , VID: V01  , SN: ART2345P0CD

NAME: "Power Supply Module 2", DESCR: "800W AC Config 1 Power Supply"
PID: PWR-C1-840WA      , VID: V01  , SN: ART2345P0CE

NAME: "Fan Tray 1", DESCR: "Fan Tray 1"
PID: C9300-FAN-F       , VID: V01  , SN: N/A
"""

    def _generate_show_environment_power(self):
        """Generar salida de show environment power"""
        psu1_status = self.power_supplies['PSU1']
        psu2_status = self.power_supplies['PSU2']

        return f"""
Power                                             Fan
Supply  Model No                Type              Status
------  ----------------------  ----------------  ------
PS1     PWR-C1-840WA            AC 800W           {psu1_status}
PS2     PWR-C1-840WA            AC 800W           {psu2_status}

PS1  800W ( 41 W allocated, 759 W available, 0 W inline power allocated)
PS2  800W ( 41 W allocated, 759 W available, 0 W inline power allocated)
"""

    def _generate_show_environment_fan(self):
        """Generar salida de show environment fan"""
        return """
Fan  Status
----  ------
FAN1  OK
FAN2  OK
FAN3  OK
"""

    def _generate_show_environment_status(self):
        """Generar salida de show environment status (9500)"""
        psu1_status = self.power_supplies['PSU1']
        psu2_status = self.power_supplies['PSU2']

        return f"""
Switch  Temp(C)  Ps1  Ps2  Status
------  -------  ---  ---  ------
  1     Normal   {psu1_status}  {psu2_status}  Healthy
"""

    def _generate_show_interfaces(self):
        """Generar salida de show interface ethernet"""
        return """
GigabitEthernet1/0/1 is up, line protocol is up (connected)
  Hardware is Gigabit Ethernet, address is 70b3.17ff.6480 (bia 70b3.17ff.6480)
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec

GigabitEthernet1/0/2 is down, line protocol is down (notconnect)
  Hardware is Gigabit Ethernet, address is 70b3.17ff.6481 (bia 70b3.17ff.6481)
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec
"""

    def disconnect_power_supply(self, psu_num):
        """Simular desconexión de fuente de poder"""
        psu_key = f'PSU{psu_num}'
        if psu_key in self.power_supplies:
            self.power_supplies[psu_key] = 'not present'
            self.psu_disconnection_count += 1
            return True
        return False

    def reconnect_power_supply(self, psu_num):
        """Simular reconexión de fuente de poder"""
        psu_key = f'PSU{psu_num}'
        if psu_key in self.power_supplies:
            self.power_supplies[psu_key] = 'OK'
            return True
        return False
