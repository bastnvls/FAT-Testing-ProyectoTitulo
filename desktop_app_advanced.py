"""
FAT Testing - Aplicación Profesional de Escritorio
Pruebas automatizadas para dispositivos Cisco vía CLI/Serial
"""

import sys
import os
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
                               QMessageBox, QFrame, QProgressBar, QGroupBox, QSplitter,
                               QStatusBar, QToolButton, QDialog, QFileDialog)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize, QUrl
from PySide6.QtGui import QFont, QTextCursor, QIcon, QDesktopServices, QKeySequence, QShortcut

# Importar módulos del proyecto
from models import db, User
from config import Config
from flask import Flask
from cisco_device_tests import DeviceTestSuite, CiscoTest
from serial_connector import SerialConnector

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

    # Aplicar estilo Corporativo
    msg_box.setStyleSheet("""
        QMessageBox {
            background-color: white;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
        }
        QMessageBox QLabel {
            color: #1e293b;
            font-size: 10pt;
            padding: 16px;
            line-height: 1.6;
            min-height: 24px;
        }
        QMessageBox QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #2563eb, stop:1 #4f46e5);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 24px;
            min-height: 36px;
            font-weight: 600;
            min-width: 80px;
            font-size: 9pt;
        }
        QMessageBox QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1d4ed8, stop:1 #4338ca);
        }
    """)

    return msg_box.exec()


class TestExecutionThread(QThread):
    """Thread para ejecutar pruebas sin bloquear la UI"""
    progress_update = Signal(int)
    log_update = Signal(str, str)  # (mensaje, tipo)
    test_complete = Signal(dict)  # Resultados de la prueba
    execution_finished = Signal()

    def __init__(self, connector, tests, parent=None):
        super().__init__(parent)
        self.connector = connector
        self.tests = tests
        self.results = []
        self.is_running = True

    def run(self):
        """Ejecutar pruebas"""
        total_tests = len(self.tests)

        for i, test in enumerate(self.tests):
            if not self.is_running:
                break

            # Actualizar progreso
            progress = int(((i + 1) / total_tests) * 100)
            self.progress_update.emit(progress)

            # Log inicio de prueba
            self.log_update.emit(
                f"\n{'─'*70}\n▸ PRUEBA {test.number}: {test.name}\n{'─'*70}\n",
                "header"
            )
            self.log_update.emit(f"Comando: {test.command}\n\n", "command")

            # Ejecutar comando
            if test.command.lower() == "reload":
                success, output = self.connector.send_special_command(test.command, "yes", 3)
            else:
                success, output = self.connector.send_command(test.command, 2)

            # Guardar resultado
            result = {
                'test_number': test.number,
                'test_name': test.name,
                'command': test.command,
                'output': output,
                'success': success,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.results.append(result)

            # Log salida
            if success:
                self.log_update.emit(output, "output")
                self.log_update.emit(f"\n✓ Prueba {test.number} completada exitosamente\n", "success")
            else:
                self.log_update.emit(f"✗ ERROR: {output}\n", "error")

            # Log fin de prueba
            self.log_update.emit(f"{'─'*70}\n\n", "header")

            self.test_complete.emit(result)

        self.execution_finished.emit()

    def stop(self):
        """Detener ejecución"""
        self.is_running = False


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

        # Logo empresarial (sin emoji)
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

        # Validación mejorada
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
                if user and user.check_password(password):
                    self.main_window = MainWindow(user)
                    self.main_window.show()
                    self.close()
                else:
                    show_message(self, "Authentication Failed", "Invalid email or password", "error")
                    self.login_button.setEnabled(True)
                    self.login_button.setText("Sign In")
                    self.password_input.clear()
                    self.password_input.setFocus()
        except Exception as e:
            show_message(self, "Connection Error", f"Database connection failed:\n{str(e)}", "error")
            self.login_button.setEnabled(True)
            self.login_button.setText("Sign In")


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.connector = None
        self.test_thread = None
        self.test_results = []

        self.setWindowTitle(f"FAT Testing Platform - {user.username}")
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

        # Splitter principal - División 2 columnas
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #e2e8f0; }")

        # Panel izquierdo: Control y configuración
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)

        # Panel derecho: Terminal y resultados
        right_panel = self.create_terminal_panel()
        splitter.addWidget(right_panel)

        # Proporción ajustada para mejor visualización
        splitter.setSizes([420, 860])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # Status bar
        self.create_status_bar()

        # Configurar atajos de teclado
        self.setup_shortcuts()

        # Cargar puertos después de crear todos los elementos UI
        self.refresh_ports()

    def create_navbar(self):
        """Crear navbar profesional empresarial"""
        navbar = QFrame()
        navbar.setObjectName("navbar")
        navbar.setFixedHeight(64)

        layout = QHBoxLayout(navbar)
        layout.setContentsMargins(32, 0, 32, 0)
        layout.setSpacing(24)

        # Logo Section
        logo_section = QHBoxLayout()
        logo_section.setSpacing(16)

        # Logo badge
        logo_badge = QFrame()
        logo_badge.setObjectName("navbarLogoBadge")
        logo_badge.setFixedSize(40, 40)
        logo_badge_layout = QVBoxLayout(logo_badge)
        logo_badge_layout.setContentsMargins(0, 0, 0, 0)
        logo_badge_layout.setAlignment(Qt.AlignCenter)

        logo_badge_text = QLabel("FT")
        logo_badge_text.setAlignment(Qt.AlignCenter)
        logo_badge_text.setFont(QFont("Segoe UI", 13, QFont.Bold))
        logo_badge_text.setObjectName("navbarLogoText")
        logo_badge_layout.addWidget(logo_badge_text)

        logo_section.addWidget(logo_badge)

        # Title and subtitle
        title_container = QVBoxLayout()
        title_container.setSpacing(2)

        title = QLabel("FAT Testing Platform")
        title.setFont(QFont("Segoe UI", 13, QFont.DemiBold))
        title.setObjectName("navbarTitle")
        title_container.addWidget(title)

        subtitle = QLabel("Field Acceptance Testing")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setObjectName("navbarSubtitle")
        title_container.addWidget(subtitle)

        logo_section.addLayout(title_container)

        layout.addLayout(logo_section)
        layout.addStretch()

        # User Section
        user_section = QHBoxLayout()
        user_section.setSpacing(16)

        # User info
        user_info_container = QVBoxLayout()
        user_info_container.setSpacing(2)
        user_info_container.setAlignment(Qt.AlignRight)

        user_name = QLabel(self.user.username.title())
        user_name.setAlignment(Qt.AlignRight)
        user_name.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        user_name.setObjectName("navbarUserName")
        user_info_container.addWidget(user_name)

        user_role = QLabel("Test Engineer")
        user_role.setAlignment(Qt.AlignRight)
        user_role.setFont(QFont("Segoe UI", 8))
        user_role.setObjectName("navbarUserRole")
        user_info_container.addWidget(user_role)

        user_section.addLayout(user_info_container)

        # Logout button
        logout_btn = QPushButton("Sign Out")
        logout_btn.setObjectName("navbarLogoutBtn")
        logout_btn.setFixedHeight(36)
        logout_btn.setFont(QFont("Segoe UI", 9, QFont.Medium))
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout)
        user_section.addWidget(logout_btn)

        layout.addLayout(user_section)

        return navbar

    def create_control_panel(self):
        """Panel de control izquierdo - Configuración Enterprise"""
        panel = QWidget()
        panel.setObjectName("controlPanel")
        panel.setMinimumWidth(380)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        # Header del panel
        header = QLabel("Test Configuration")
        header.setFont(QFont("Segoe UI", 14, QFont.DemiBold))
        header.setObjectName("panelHeader")
        layout.addWidget(header)

        # Estado de conexión
        self.connection_status = QFrame()
        self.connection_status.setObjectName("statusCard")
        status_layout = QHBoxLayout(self.connection_status)
        status_layout.setContentsMargins(16, 12, 16, 12)
        status_layout.setSpacing(12)

        # Status indicator (círculo sin emoji)
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(10, 10)
        self.status_indicator.setObjectName("statusIndicator")
        self.status_indicator.setStyleSheet("""
            background-color: #94a3b8;
            border-radius: 5px;
        """)
        status_layout.addWidget(self.status_indicator)

        self.status_label = QLabel("Disconnected")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        layout.addWidget(self.connection_status)

        # Configuración de dispositivo
        device_group = QGroupBox("Device Configuration")
        device_group.setObjectName("configGroup")
        device_layout = QVBoxLayout()
        device_layout.setSpacing(10)
        device_layout.setContentsMargins(16, 20, 16, 16)

        device_label = QLabel("Device Model")
        device_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        device_label.setObjectName("configLabel")
        device_layout.addWidget(device_label)

        self.device_combo = QComboBox()
        self.device_combo.setObjectName("configCombo")
        self.device_combo.addItems(DeviceTestSuite.get_device_models())
        self.device_combo.setFont(QFont("Segoe UI", 10))
        self.device_combo.setFixedHeight(42)
        device_layout.addWidget(self.device_combo)

        device_group.setLayout(device_layout)
        layout.addWidget(device_group)

        # Configuración serial
        serial_group = QGroupBox("Serial Connection")
        serial_group.setObjectName("configGroup")
        serial_layout = QVBoxLayout()
        serial_layout.setSpacing(14)
        serial_layout.setContentsMargins(16, 20, 16, 16)

        # Puerto COM con opciones
        port_label = QLabel("COM Port")
        port_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        port_label.setObjectName("configLabel")
        serial_layout.addWidget(port_label)

        port_layout = QHBoxLayout()
        port_layout.setSpacing(10)

        self.port_combo = QComboBox()
        self.port_combo.setObjectName("configCombo")
        self.port_combo.setEditable(True)
        self.port_combo.setFont(QFont("Segoe UI", 10))
        self.port_combo.setFixedHeight(42)
        self.port_combo.setPlaceholderText("Select or enter COM port...")
        port_layout.addWidget(self.port_combo, 1)

        # Botón refresh sin emoji
        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("secondaryBtn")
        refresh_button.setFixedSize(80, 42)
        refresh_button.setFont(QFont("Segoe UI", 9, QFont.Medium))
        refresh_button.setCursor(Qt.PointingHandCursor)
        refresh_button.clicked.connect(self.refresh_ports)
        port_layout.addWidget(refresh_button)

        serial_layout.addLayout(port_layout)

        # Velocidad (Baud Rate)
        baud_label = QLabel("Baud Rate")
        baud_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        baud_label.setObjectName("configLabel")
        serial_layout.addWidget(baud_label)

        self.baud_combo = QComboBox()
        self.baud_combo.setObjectName("configCombo")
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        self.baud_combo.setFont(QFont("Segoe UI", 10))
        self.baud_combo.setFixedHeight(42)
        serial_layout.addWidget(self.baud_combo)

        serial_group.setLayout(serial_layout)
        layout.addWidget(serial_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Info de progreso
        self.progress_label = QLabel("Ready to start")
        self.progress_label.setFont(QFont("Segoe UI", 9))
        self.progress_label.setObjectName("progressLabel")
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)

        layout.addStretch()

        # Action Buttons Section
        action_header = QLabel("Actions")
        action_header.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        action_header.setObjectName("sectionHeader")
        layout.addWidget(action_header)

        # Botón principal - Start
        self.start_button = QPushButton("Run Tests")
        self.start_button.setObjectName("primaryActionBtn")
        self.start_button.setMinimumHeight(46)
        self.start_button.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.clicked.connect(self.start_tests)
        layout.addWidget(self.start_button)

        # Botones secundarios
        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("dangerBtn")
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setFont(QFont("Segoe UI", 9, QFont.Medium))
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.clicked.connect(self.stop_tests)
        button_row.addWidget(self.stop_button)

        self.export_button = QPushButton("Export")
        self.export_button.setObjectName("secondaryBtn")
        self.export_button.setMinimumHeight(40)
        self.export_button.setFont(QFont("Segoe UI", 9, QFont.Medium))
        self.export_button.setCursor(Qt.PointingHandCursor)
        self.export_button.clicked.connect(self.export_log)
        button_row.addWidget(self.export_button)

        layout.addLayout(button_row)

        return panel

    def create_terminal_panel(self):
        """Panel derecho - Terminal y resultados"""
        panel = QWidget()
        panel.setObjectName("terminalPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        terminal_header = QLabel("Execution Log")
        terminal_header.setFont(QFont("Segoe UI", 14, QFont.DemiBold))
        terminal_header.setObjectName("panelHeader")
        header_layout.addWidget(terminal_header)

        header_layout.addStretch()

        clear_button = QPushButton("Clear")
        clear_button.setObjectName("secondaryBtn")
        clear_button.setFixedHeight(36)
        clear_button.setFixedWidth(80)
        clear_button.setFont(QFont("Segoe UI", 9, QFont.Medium))
        clear_button.setCursor(Qt.PointingHandCursor)
        clear_button.clicked.connect(lambda: self.terminal.clear())
        header_layout.addWidget(clear_button)

        layout.addLayout(header_layout)

        # Terminal output
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont("Consolas", 10))
        self.terminal.setLineWrapMode(QTextEdit.WidgetWidth)
        self.terminal.setStyleSheet("""
            QTextEdit {
                background-color: #fafbfc;
                color: #1e293b;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                padding: 20px;
                line-height: 1.7;
            }
            QTextEdit:focus {
                border-color: #2563eb;
            }
        """)

        # Mensaje inicial
        self.terminal.setHtml("""
            <div style='color: #64748b; text-align: center; padding: 48px 32px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;'>
                <p style='font-size: 15px; font-weight: 600; margin-bottom: 12px; color: #1a56db; line-height: 1.6;'>
                    System Ready
                </p>
                <p style='font-size: 11px; color: #64748b; line-height: 1.7;'>
                    Configure device and COM port settings<br>
                    Then click <strong>RUN TESTS</strong> to begin
                </p>
            </div>
        """)

        layout.addWidget(self.terminal, 1)

        # Resultados resumidos
        results_header = QLabel("Test Summary")
        results_header.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        results_header.setObjectName("sectionHeader")
        layout.addWidget(results_header)

        self.results_summary = QLabel("No tests executed")
        self.results_summary.setFont(QFont("Segoe UI", 10))
        self.results_summary.setObjectName("resultsCard")
        self.results_summary.setWordWrap(True)
        self.results_summary.setAlignment(Qt.AlignCenter)
        self.results_summary.setMinimumHeight(56)
        layout.addWidget(self.results_summary)

        return panel

    def create_status_bar(self):
        """Crear barra de estado profesional"""
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: white;
                color: #64748b;
                border-top: 1px solid #e2e8f0;
                padding: 4px 12px;
            }
        """)
        self.status_bar.setFont(QFont("Segoe UI", 9))
        self.status_bar.showMessage("● Listo")
        self.setStatusBar(self.status_bar)

    def setup_shortcuts(self):
        """Configurar atajos de teclado para accesibilidad"""
        # F5 - Iniciar pruebas
        start_shortcut = QShortcut(QKeySequence("F5"), self)
        start_shortcut.activated.connect(lambda: self.start_button.click() if self.start_button.isEnabled() else None)

        # Escape - Detener pruebas
        stop_shortcut = QShortcut(QKeySequence("Escape"), self)
        stop_shortcut.activated.connect(lambda: self.stop_button.click() if self.stop_button.isEnabled() else None)

        # Ctrl+E - Exportar
        export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        export_shortcut.activated.connect(self.export_log)

        # Ctrl+R - Refrescar puertos
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self.refresh_ports)

        # Ctrl+L - Limpiar terminal
        clear_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        clear_shortcut.activated.connect(lambda: self.terminal.clear())

        # Ctrl+Q - Cerrar sesión
        logout_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        logout_shortcut.activated.connect(self.logout)

        # Actualizar tooltips con atajos
        self.start_button.setToolTip("Connect to device and run FAT test suite (F5)")
        self.stop_button.setToolTip("Stop test execution (Esc)")
        self.export_button.setToolTip("Save test results to file (Ctrl+E)")

    def refresh_ports(self):
        """Refrescar lista de puertos COM con validación"""
        self.port_combo.clear()
        ports = SerialConnector.list_available_ports()

        if ports:
            for port in ports:
                self.port_combo.addItem(f"{port['device']} - {port['description']}")

            # Actualizar estado de conexión - Dispositivo detectado
            self.status_indicator.setStyleSheet("color: #f59e0b; font-size: 14px;")
            self.status_label.setText("Dispositivo detectado")
            self.status_label.setStyleSheet("color: #f59e0b; font-weight: 600;")

            # Actualizar status bar si existe
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(f"✓ {len(ports)} puerto(s) COM disponible(s)")

            # Habilitar botón de inicio
            self.start_button.setEnabled(True)

        else:
            self.port_combo.addItem("No hay dispositivos - Conecte uno y presione ⟲")
            self.port_combo.setCurrentIndex(0)

            # Actualizar estado de conexión - Sin dispositivo
            self.status_indicator.setStyleSheet("color: #dc2626; font-size: 14px;")
            self.status_label.setText("Sin dispositivo")
            self.status_label.setStyleSheet("color: #dc2626; font-weight: 600;")

            # Actualizar status bar si existe
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage("⚠ No hay puertos COM - Conecte dispositivo y presione ⟲")

            self.start_button.setEnabled(False)

    def start_tests(self):
        """Iniciar ejecución de pruebas con validación robusta"""
        # Validación 1: Puerto válido
        if not self.port_combo.currentText() or "No hay dispositivos" in self.port_combo.currentText():
            show_message(
                self,
                "Sin Dispositivo",
                "Conecte un dispositivo y presione el botón de actualizar (⟲)",
                "warning"
            )
            return

        # Limpiar terminal
        self.terminal.clear()

        # Conectar al dispositivo
        device_model = self.device_combo.currentText()
        port = self.port_combo.currentText().split(" - ")[0]
        baud_rate = int(self.baud_combo.currentText())

        # Actualizar UI
        self.status_indicator.setStyleSheet("color: #2563eb; font-size: 14px;")
        self.status_label.setText("Conectando...")
        self.status_label.setStyleSheet("color: #2563eb; font-weight: 600;")
        self.status_bar.showMessage(f"● Estableciendo conexión con {port}...")

        self.connector = SerialConnector(port=port, baudrate=baud_rate)
        self.append_log(f"▸ Conectando a {port} @ {baud_rate} baud...\n", "info")

        success, message = self.connector.connect()

        # Validación 2: Conexión exitosa
        if not success:
            self.status_indicator.setStyleSheet("color: #dc2626; font-size: 14px;")
            self.status_label.setText("Conexión fallida")
            self.status_label.setStyleSheet("color: #dc2626; font-weight: 600;")
            self.status_bar.showMessage(f"● Conexión fallida - {message}")

            show_message(
                self,
                "Conexión Fallida",
                f"No se pudo conectar al dispositivo.\n\n{message}\n\n"
                "Verifique:\n"
                "• Dispositivo encendido y listo\n"
                "• Puerto COM correcto\n"
                "• Ninguna aplicación usa el puerto\n"
                "• Velocidad (baud rate) correcta",
                "error"
            )
            return

        # Conexión exitosa
        self.status_indicator.setStyleSheet("color: #10b981; font-size: 14px;")
        self.status_label.setText("Conectado")
        self.status_label.setStyleSheet("color: #10b981; font-weight: 600;")
        self.status_bar.showMessage(f"● Conectado a {port} @ {baud_rate} baud")

        self.append_log(f"✓ {message}\n", "success")
        self.append_log(f"▸ Modelo de Dispositivo: {device_model}\n", "info")
        self.append_log(f"▸ Iniciando suite de pruebas...\n\n", "info")

        # Obtener pruebas
        tests = DeviceTestSuite.get_tests_for_device(device_model)
        self.progress_label.setText(f"Ejecutando: 0/{len(tests)} pruebas")

        # Deshabilitar botón start, habilitar stop
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # Iniciar thread de ejecución
        self.test_thread = TestExecutionThread(self.connector, tests)
        self.test_thread.progress_update.connect(self.update_progress)
        self.test_thread.log_update.connect(self.append_log)
        self.test_thread.test_complete.connect(self.on_test_complete)
        self.test_thread.execution_finished.connect(self.on_execution_finished)
        self.test_thread.start()

    def stop_tests(self):
        """Detener pruebas"""
        if self.test_thread and self.test_thread.isRunning():
            self.test_thread.stop()
            self.append_log("\n▸ Deteniendo ejecución de pruebas...\n", "warning")
            self.status_bar.showMessage("● Ejecución de pruebas detenida por el usuario")

    def update_progress(self, value):
        """Actualizar barra de progreso y etiqueta"""
        self.progress_bar.setValue(value)

        # Calcular número de pruebas completadas
        if hasattr(self, 'test_thread') and self.test_thread:
            total = len(self.test_thread.tests)
            completed = int((value / 100) * total)
            self.progress_label.setText(f"Ejecutando: {completed}/{total} pruebas")
            self.status_bar.showMessage(f"● Progreso: {value}% ({completed}/{total})")

    def append_log(self, message, log_type="output"):
        """Agregar mensaje al terminal con colores"""
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Colores según tipo - Landing Page palette
        colors = {
            "header": "#f59e0b",  # Amber para headers
            "info": "#2563eb",    # Blue-600 para info
            "success": "#10b981", # Emerald-500 para success
            "error": "#dc2626",   # Red-600 para errores
            "warning": "#f59e0b", # Amber-500 para warnings
            "command": "#7c3aed", # Violet-600 para comandos
            "output": "#1e293b"   # Gray-900 para output
        }

        color = colors.get(log_type, "#475569")

        # Insertar con color
        cursor.insertHtml(f'<span style="color: {color}; font-weight: 500;">{message.replace("\n", "<br>")}</span>')

        self.terminal.setTextCursor(cursor)
        self.terminal.ensureCursorVisible()

    def on_test_complete(self, result):
        """Cuando se completa una prueba"""
        self.test_results.append(result)

    def on_execution_finished(self):
        """Cuando terminan todas las pruebas"""
        self.append_log("\n✓ Todas las pruebas completadas exitosamente\n", "success")

        # Calcular estadísticas
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['success'])
        failed = total - passed

        # Actualizar resumen
        summary_text = f"Total: {total} pruebas  |  Exitosas: {passed}  |  Fallidas: {failed}"
        if failed == 0:
            self.results_summary.setText(summary_text)
            self.results_summary.setStyleSheet("""
                background-color: #d1fae5;
                color: #065f46;
                padding: 16px;
                border-radius: 8px;
                border: 2px solid #10b981;
                font-weight: 600;
                font-size: 10pt;
                line-height: 1.6;
            """)
        else:
            self.results_summary.setText(summary_text)
            self.results_summary.setStyleSheet("""
                background-color: #fef3c7;
                color: #92400e;
                padding: 16px;
                border-radius: 8px;
                border: 2px solid #f59e0b;
                font-weight: 600;
                font-size: 10pt;
                line-height: 1.6;
            """)

        # Desconectar
        if self.connector:
            self.connector.disconnect()

        # Actualizar UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(100)
        self.progress_label.setText(f"Completado: {total} pruebas")

        self.status_indicator.setStyleSheet("color: #10b981; font-size: 14px;")
        self.status_label.setText("Pruebas completadas")
        self.status_label.setStyleSheet("color: #10b981; font-weight: 600;")
        self.status_bar.showMessage(f"● Ejecución completa - {passed}/{total} exitosas")

        # Notificación
        show_message(
            self,
            "Pruebas Completadas",
            f"Resultados: {passed}/{total} exitosas, {failed} fallidas\n\n"
            f"Use el botón EXPORTAR para guardar el reporte.",
            "success"
        )

    def logout(self):
        """Cerrar sesión y volver al login"""
        reply = show_message(
            self,
            "Cerrar Sesión",
            f"¿Estás seguro que deseas cerrar sesión, {self.user.username.title()}?",
            "warning"
        )

        # Si el usuario confirma, cerrar ventana y mostrar login
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

    def export_log(self):
        """Exportar log de pruebas con diálogo de archivo"""
        if not self.test_results:
            show_message(self, "Sin Resultados", "No hay resultados para exportar", "warning")
            return

        # Generar nombre de archivo sugerido
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"FAT_Test_Results_{timestamp}.txt"

        # Abrir diálogo para elegir ubicación y nombre
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte de Pruebas",
            default_filename,
            "Archivos de Texto (*.txt);;Todos los archivos (*.*)"
        )

        # Si el usuario canceló el diálogo
        if not filename:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("FAT TESTING - RESULTADOS DE PRUEBAS\n")
                f.write("="*80 + "\n\n")
                f.write(f"Usuario: {self.user.username}\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Dispositivo: {self.device_combo.currentText()}\n")
                f.write(f"Puerto: {self.port_combo.currentText()}\n")
                f.write("\n" + "="*80 + "\n\n")

                for result in self.test_results:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"# INICIO PRUEBA {result['test_number']}\n")
                    f.write(f"{'='*80}\n")
                    f.write(f"Nombre: {result['test_name']}\n")
                    f.write(f"Comando: {result['command']}\n")
                    f.write(f"Timestamp: {result['timestamp']}\n")
                    f.write(f"\nSalida:\n{'-'*80}\n")
                    f.write(result['output'])
                    f.write(f"\n{'-'*80}\n")
                    f.write(f"# FIN PRUEBA {result['test_number']}\n")
                    f.write(f"{'='*80}\n\n")

            # Obtener solo el nombre del archivo sin la ruta completa
            import os
            file_basename = os.path.basename(filename)

            show_message(
                self,
                "Exportación Exitosa",
                f"Reporte guardado exitosamente:\n{file_basename}",
                "success"
            )

        except Exception as e:
            show_message(self, "Error de Exportación", f"Error al guardar archivo:\n{str(e)}", "error")

    def apply_styles(self):
        """Aplicar estilos corporativos profesionales Enterprise"""
        self.setStyleSheet("""
            /* ========== GLOBAL STYLES ========== */
            QMainWindow {
                background-color: #f1f5f9;
            }

            /* ========== NAVBAR ========== */
            QFrame#navbar {
                background-color: #1a56db;
                border-bottom: 1px solid #1e40af;
            }

            QFrame#navbarLogoBadge {
                background-color: #ffffff;
                border-radius: 8px;
            }

            QLabel#navbarLogoText {
                color: #1a56db;
            }

            QLabel#navbarTitle {
                color: #ffffff;
            }

            QLabel#navbarSubtitle {
                color: #dbeafe;
            }

            QLabel#navbarUserName {
                color: #ffffff;
            }

            QLabel#navbarUserRole {
                color: #bfdbfe;
            }

            QPushButton#navbarLogoutBtn {
                background-color: rgba(255, 255, 255, 0.12);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 0 16px;
                font-weight: 500;
            }

            QPushButton#navbarLogoutBtn:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.4);
            }

            QPushButton#navbarLogoutBtn:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }

            /* ========== PANELS ========== */
            QWidget#controlPanel {
                background-color: #ffffff;
                border-right: 1px solid #e2e8f0;
            }

            QWidget#terminalPanel {
                background-color: #ffffff;
            }

            /* ========== HEADERS ========== */
            QLabel#panelHeader {
                color: #0f172a;
                font-weight: 600;
            }

            QLabel#sectionHeader {
                color: #334155;
                font-weight: 600;
                margin-top: 4px;
            }

            /* ========== STATUS CARD ========== */
            QFrame#statusCard {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }

            QLabel#statusLabel {
                color: #64748b;
            }

            /* ========== GROUP BOXES ========== */
            QGroupBox#configGroup {
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 28px;
                background-color: #fafbfc;
                font-size: 10pt;
                font-weight: 600;
            }

            QGroupBox#configGroup::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                top: 8px;
                padding: 7px 14px;
                background-color: #1a56db;
                color: white;
                border-radius: 6px;
                font-size: 9pt;
                font-weight: 600;
                letter-spacing: 0.3px;
            }

            /* ========== LABELS ========== */
            QLabel#configLabel {
                color: #475569;
                font-weight: 500;
            }

            QLabel#progressLabel {
                color: #64748b;
                font-weight: 400;
            }

            /* ========== PRIMARY ACTION BUTTON ========== */
            QPushButton#primaryActionBtn {
                background-color: #1a56db;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                padding: 0 20px;
                letter-spacing: 0.3px;
            }

            QPushButton#primaryActionBtn:hover {
                background-color: #1e40af;
            }

            QPushButton#primaryActionBtn:pressed {
                background-color: #1e3a8a;
            }

            QPushButton#primaryActionBtn:disabled {
                background-color: #cbd5e1;
                color: #94a3b8;
            }

            /* ========== SECONDARY BUTTON ========== */
            QPushButton#secondaryBtn {
                background-color: #ffffff;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 0 16px;
                font-weight: 500;
            }

            QPushButton#secondaryBtn:hover {
                background-color: #f8fafc;
                border-color: #94a3b8;
                color: #1e293b;
            }

            QPushButton#secondaryBtn:pressed {
                background-color: #f1f5f9;
            }

            /* ========== DANGER BUTTON ========== */
            QPushButton#dangerBtn {
                background-color: #ffffff;
                color: #dc2626;
                border: 1px solid #fca5a5;
                border-radius: 6px;
                padding: 0 16px;
                font-weight: 500;
            }

            QPushButton#dangerBtn:hover {
                background-color: #fee2e2;
                border-color: #f87171;
            }

            QPushButton#dangerBtn:pressed {
                background-color: #fecaca;
            }

            QPushButton#dangerBtn:disabled {
                background-color: #f8fafc;
                color: #cbd5e1;
                border-color: #e2e8f0;
            }

            /* ========== COMBOBOX ========== */
            QComboBox#configCombo {
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 0 16px;
                background-color: white;
                color: #0f172a;
                font-size: 10pt;
                selection-background-color: #1a56db;
                selection-color: white;
            }

            QComboBox#configCombo:focus {
                border-color: #1a56db;
                background-color: #f8fafc;
            }

            QComboBox#configCombo:hover {
                border-color: #94a3b8;
            }

            QComboBox#configCombo::drop-down {
                border: none;
                width: 30px;
            }

            QComboBox#configCombo::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #64748b;
            }

            QComboBox#configCombo QAbstractItemView {
                background-color: white;
                color: #0f172a;
                selection-background-color: #1a56db;
                selection-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                outline: none;
                padding: 4px;
            }

            QComboBox#configCombo QAbstractItemView::item {
                min-height: 36px;
                padding: 8px 12px;
            }

            /* ========== PROGRESS BAR ========== */
            QProgressBar#progressBar {
                border: none;
                border-radius: 3px;
                background-color: #e2e8f0;
                text-align: center;
            }

            QProgressBar#progressBar::chunk {
                background-color: #1a56db;
                border-radius: 3px;
            }

            /* ========== RESULTS CARD ========== */
            QLabel#resultsCard {
                background-color: #f8fafc;
                color: #64748b;
                padding: 16px;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
            }

            /* ========== TOOLTIPS ========== */
            QToolTip {
                background-color: #0f172a;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 9pt;
            }

            /* ========== SCROLL BARS ========== */
            QScrollBar:vertical {
                background-color: #f8fafc;
                width: 10px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background-color: #cbd5e1;
                border-radius: 5px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #94a3b8;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar:horizontal {
                background-color: #f8fafc;
                height: 10px;
                border-radius: 5px;
            }

            QScrollBar::handle:horizontal {
                background-color: #cbd5e1;
                border-radius: 5px;
                min-width: 30px;
            }

            QScrollBar::handle:horizontal:hover {
                background-color: #94a3b8;
            }

            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }

            /* ========== STATUS BAR ========== */
            QStatusBar {
                background-color: #ffffff;
                color: #64748b;
                border-top: 1px solid #e2e8f0;
                font-size: 9pt;
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
