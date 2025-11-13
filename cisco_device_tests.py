"""
Definiciones de pruebas FAT para dispositivos Cisco
"""

class CiscoTest:
    """Clase base para una prueba"""
    def __init__(self, number, name, command, requires_manual=False, manual_steps=None):
        self.number = number
        self.name = name
        self.command = command
        self.requires_manual = requires_manual
        self.manual_steps = manual_steps or []
        self.repetitions = 1  # Número de veces que se ejecuta

class DeviceTestSuite:
    """Suite de pruebas para un dispositivo específico"""

    @staticmethod
    def get_tests_for_device(device_model):
        """Retorna lista de pruebas según el modelo"""
        if device_model == "Cisco 9200":
            return DeviceTestSuite.cisco_9200_tests()
        elif device_model == "Cisco 9300":
            return DeviceTestSuite.cisco_9300_tests()
        elif device_model == "Cisco 9500":
            return DeviceTestSuite.cisco_9500_tests()
        else:
            return []

    @staticmethod
    def cisco_9200_tests():
        """Pruebas para Cisco 9200"""
        return [
            CiscoTest(
                number=1,
                name="Verificación de Versión",
                command="show version",
                requires_manual=False
            ),
            CiscoTest(
                number=2,
                name="Inventario Básico",
                command="show inventory",
                requires_manual=False
            ),
            CiscoTest(
                number=3,
                name="Estado de Fuentes de Poder",
                command="show environment power",
                requires_manual=True,
                manual_steps=[
                    "Ejecutar comando inicial con ambas fuentes conectadas",
                    "Desconectar PSU1 (Fuente 1) y ejecutar comando",
                    "Reconectar PSU1 y desconectar PSU2 (Fuente 2), ejecutar comando",
                    "Reconectar PSU2 y verificar que ambas aparezcan OK"
                ]
            ),
            CiscoTest(
                number=4,
                name="Estado de Ventiladores",
                command="show environment fan",
                requires_manual=False
            ),
            CiscoTest(
                number=5,
                name="Prueba de Reload",
                command="reload",
                requires_manual=True,
                manual_steps=[
                    "El dispositivo se reiniciará",
                    "Espere a que el dispositivo vuelva a estar disponible (~5 minutos)",
                    "Deberá volver a conectarse después del reload"
                ]
            ),
            CiscoTest(
                number=6,
                name="Modo Enable",
                command="enable",
                requires_manual=False
            ),
            CiscoTest(
                number=7,
                name="Inventario Completo",
                command="show inventory all",
                requires_manual=False
            ),
            CiscoTest(
                number=8,
                name="Interfaces Ethernet",
                command="show interface ethernet",
                requires_manual=False
            ),
        ]

    @staticmethod
    def cisco_9300_tests():
        """Pruebas para Cisco 9300"""
        return [
            CiscoTest(
                number=1,
                name="Verificación de Versión",
                command="show version",
                requires_manual=False
            ),
            CiscoTest(
                number=2,
                name="Inventario Básico",
                command="show inventory",
                requires_manual=False
            ),
            CiscoTest(
                number=3,
                name="Estado de Fuentes de Poder",
                command="show environment power",
                requires_manual=True,
                manual_steps=[
                    "Ejecutar comando inicial con ambas fuentes conectadas",
                    "Desconectar PSU1 (Fuente 1) y ejecutar comando",
                    "Reconectar PSU1 y desconectar PSU2 (Fuente 2), ejecutar comando",
                    "Reconectar PSU2 y verificar que ambas aparezcan OK"
                ]
            ),
            CiscoTest(
                number=4,
                name="Estado de Ventiladores",
                command="show environment fan",
                requires_manual=False
            ),
            CiscoTest(
                number=5,
                name="Prueba de Reload",
                command="reload",
                requires_manual=True,
                manual_steps=[
                    "El dispositivo se reiniciará",
                    "Espere a que el dispositivo vuelva a estar disponible (~5 minutos)",
                    "Deberá volver a conectarse después del reload"
                ]
            ),
            CiscoTest(
                number=6,
                name="Modo Enable",
                command="enable",
                requires_manual=False
            ),
            CiscoTest(
                number=7,
                name="Inventario Completo",
                command="show inventory all",
                requires_manual=False
            ),
            CiscoTest(
                number=8,
                name="Interfaces Ethernet",
                command="show interface ethernet",
                requires_manual=False
            ),
        ]

    @staticmethod
    def cisco_9500_tests():
        """Pruebas para Cisco 9500"""
        return [
            CiscoTest(
                number=1,
                name="Verificación de Versión",
                command="show version",
                requires_manual=False
            ),
            CiscoTest(
                number=2,
                name="Inventario Básico",
                command="show inventory",
                requires_manual=False
            ),
            CiscoTest(
                number=3,
                name="Estado del Sistema",
                command="show environment status",
                requires_manual=False
            ),
            CiscoTest(
                number=4,
                name="Prueba de Reload",
                command="reload",
                requires_manual=True,
                manual_steps=[
                    "El dispositivo se reiniciará",
                    "Espere a que el dispositivo vuelva a estar disponible (~5 minutos)",
                    "Deberá volver a conectarse después del reload"
                ]
            ),
            CiscoTest(
                number=5,
                name="Modo Enable",
                command="enable",
                requires_manual=False
            ),
            CiscoTest(
                number=6,
                name="Inventario Completo",
                command="show inventory all",
                requires_manual=False
            ),
            CiscoTest(
                number=7,
                name="Interfaces Ethernet",
                command="show interface ethernet",
                requires_manual=False
            ),
        ]

    @staticmethod
    def get_device_models():
        """Retorna lista de modelos soportados"""
        return ["Cisco 9200", "Cisco 9300", "Cisco 9500"]
