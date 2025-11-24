import sys
import os
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QMessageBox, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

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
        """Panel de contenido principal"""
        panel = QWidget()
        panel.setObjectName("contentPanel")
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(30)

        # Card de bienvenida
        welcome_card = QFrame()
        welcome_card.setObjectName("welcomeCard")
        welcome_card.setFixedWidth(600)
        card_layout = QVBoxLayout(welcome_card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(24)

        # Título de bienvenida
        welcome_title = QLabel(f"Welcome, {self.user_display_name.title()}!")
        welcome_title.setAlignment(Qt.AlignCenter)
        welcome_title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        welcome_title.setObjectName("welcomeTitle")
        card_layout.addWidget(welcome_title)

        # Subtítulo
        welcome_subtitle = QLabel("FAT Testing Platform")
        welcome_subtitle.setAlignment(Qt.AlignCenter)
        welcome_subtitle.setFont(QFont("Segoe UI", 14))
        welcome_subtitle.setObjectName("welcomeSubtitle")
        card_layout.addWidget(welcome_subtitle)

        # Descripción
        welcome_description = QLabel(
            "This is the main application interface.\n"
            "The testing functionalities will be implemented here."
        )
        welcome_description.setAlignment(Qt.AlignCenter)
        welcome_description.setFont(QFont("Segoe UI", 11))
        welcome_description.setObjectName("welcomeDescription")
        welcome_description.setWordWrap(True)
        card_layout.addWidget(welcome_description)

        layout.addWidget(welcome_card, alignment=Qt.AlignCenter)

        return panel

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
                background-color: #ffffff;
            }

            /* ========== WELCOME CARD ========== */
            QFrame#welcomeCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }

            QLabel#welcomeTitle {
                color: #0f172a;
            }

            QLabel#welcomeSubtitle {
                color: #1a56db;
            }

            QLabel#welcomeDescription {
                color: #64748b;
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
