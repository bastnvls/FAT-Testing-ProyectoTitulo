"""
FAT Testing - Aplicación de Escritorio con PySide6
Aplicación de login que se conecta a la misma base de datos que la aplicación web
"""

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QMessageBox, QFrame)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon

# Importar modelos y configuración
from models import db, User
from config import Config
from flask import Flask

# Configurar aplicación Flask para acceso a la base de datos
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FAT Testing - Login")
        self.setFixedSize(450, 550)
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        """Configurar interfaz de usuario"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(0)

        # Card contenedor
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(150)
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)

        # Icono
        icon_label = QLabel("🔒")
        icon_label.setObjectName("icon")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_font = QFont("Segoe UI Emoji", 32)
        icon_label.setFont(icon_font)
        header_layout.addWidget(icon_label)

        # Título
        title = QLabel("Bienvenido")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont("Inter", 20, QFont.Bold)
        title.setFont(title_font)
        header_layout.addWidget(title)

        # Subtítulo
        subtitle = QLabel("Inicia sesión en FAT Testing")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle_font = QFont("Inter", 10)
        subtitle.setFont(subtitle_font)
        header_layout.addWidget(subtitle)

        card_layout.addWidget(header)

        # Body
        body = QFrame()
        body.setObjectName("body")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(30, 30, 30, 30)
        body_layout.setSpacing(10)

        # Email label
        email_label = QLabel("📧 Correo Electrónico")
        email_label.setObjectName("fieldLabel")
        email_font = QFont("Inter", 10, QFont.Bold)
        email_label.setFont(email_font)
        body_layout.addWidget(email_label)

        # Email input
        self.email_input = QLineEdit()
        self.email_input.setObjectName("input")
        self.email_input.setPlaceholderText("tu@email.com")
        self.email_input.setFixedHeight(45)
        input_font = QFont("Inter", 11)
        self.email_input.setFont(input_font)
        body_layout.addWidget(self.email_input)

        body_layout.addSpacing(10)

        # Password label
        password_label = QLabel("🔑 Contraseña")
        password_label.setObjectName("fieldLabel")
        password_label.setFont(email_font)
        body_layout.addWidget(password_label)

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setObjectName("input")
        self.password_input.setPlaceholderText("Tu contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(45)
        self.password_input.setFont(input_font)
        self.password_input.returnPressed.connect(self.login)
        body_layout.addWidget(self.password_input)

        body_layout.addSpacing(15)

        # Login button
        self.login_button = QPushButton("🔓 Iniciar Sesión")
        self.login_button.setObjectName("loginButton")
        self.login_button.setFixedHeight(50)
        button_font = QFont("Inter", 12, QFont.Bold)
        self.login_button.setFont(button_font)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.login)
        body_layout.addWidget(self.login_button)

        body_layout.addSpacing(10)

        # Footer
        footer = QLabel("🛡️ Tus datos están protegidos y encriptados")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignCenter)
        footer_font = QFont("Inter", 8)
        footer.setFont(footer_font)
        body_layout.addWidget(footer)

        body_layout.addStretch()

        card_layout.addWidget(body)
        main_layout.addWidget(card)

    def apply_styles(self):
        """Aplicar estilos CSS"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f4f8;
            }

            QFrame#card {
                background-color: white;
                border-radius: 12px;
            }

            QFrame#header {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4F46E5,
                    stop:1 #7C3AED
                );
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }

            QFrame#header QLabel#icon {
                color: white;
            }

            QFrame#header QLabel#title {
                color: white;
            }

            QFrame#header QLabel#subtitle {
                color: #E0E7FF;
            }

            QFrame#body {
                background-color: white;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }

            QLabel#fieldLabel {
                color: #1F2937;
            }

            QLineEdit#input {
                border: 2px solid #D1D5DB;
                border-radius: 8px;
                padding: 10px;
                background-color: white;
                color: #1F2937;
            }

            QLineEdit#input:focus {
                border: 2px solid #4F46E5;
            }

            QPushButton#loginButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4F46E5,
                    stop:1 #7C3AED
                );
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }

            QPushButton#loginButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4338CA,
                    stop:1 #6D28D9
                );
            }

            QPushButton#loginButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3730A3,
                    stop:1 #5B21B6
                );
            }

            QPushButton#loginButton:disabled {
                background: #9CA3AF;
            }

            QLabel#footer {
                color: #6B7280;
            }
        """)

    def login(self):
        """Procesar login"""
        email = self.email_input.text().strip()
        password = self.password_input.text()

        # Validar campos
        if not email:
            QMessageBox.warning(self, "Error", "Por favor ingresa tu correo electrónico")
            return

        if not password:
            QMessageBox.warning(self, "Error", "Por favor ingresa tu contraseña")
            return

        # Deshabilitar botón mientras se procesa
        self.login_button.setEnabled(False)
        self.login_button.setText("Verificando...")

        try:
            # Verificar credenciales en la base de datos
            with app.app_context():
                user = User.query.filter_by(email=email).first()

                if user and user.check_password(password):
                    # Login exitoso
                    self.show_welcome_screen(user)
                else:
                    # Credenciales incorrectas
                    QMessageBox.critical(
                        self,
                        "Error de autenticación",
                        "Correo o contraseña incorrectos.\nPor favor verifica tus credenciales."
                    )
                    self.login_button.setEnabled(True)
                    self.login_button.setText("🔓 Iniciar Sesión")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de conexión",
                f"No se pudo conectar a la base de datos.\n\nError: {str(e)}"
            )
            self.login_button.setEnabled(True)
            self.login_button.setText("🔓 Iniciar Sesión")

    def show_welcome_screen(self, user):
        """Mostrar pantalla de bienvenida"""
        # Crear nueva ventana de bienvenida
        self.welcome_window = WelcomeWindow(user)
        self.welcome_window.show()
        self.close()


class WelcomeWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle("FAT Testing - Bienvenido")
        self.setFixedSize(500, 400)
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        """Configurar interfaz de usuario"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(0)

        # Card contenedor
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # Header success
        header = QFrame()
        header.setObjectName("successHeader")
        header.setFixedHeight(120)
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)

        # Icono de éxito
        icon_label = QLabel("✅")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_font = QFont("Segoe UI Emoji", 40)
        icon_label.setFont(icon_font)
        header_layout.addWidget(icon_label)

        # Título
        title = QLabel("¡Inicio de Sesión Exitoso!")
        title.setObjectName("successTitle")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont("Inter", 16, QFont.Bold)
        title.setFont(title_font)
        header_layout.addWidget(title)

        card_layout.addWidget(header)

        # Body
        body = QFrame()
        body.setObjectName("body")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(30, 30, 30, 30)
        body_layout.setSpacing(10)

        body_layout.addSpacing(20)

        # Mensaje de bienvenida
        welcome = QLabel(f"Hola, {self.user.username}!")
        welcome.setObjectName("welcomeText")
        welcome.setAlignment(Qt.AlignCenter)
        welcome_font = QFont("Inter", 24, QFont.Bold)
        welcome.setFont(welcome_font)
        body_layout.addWidget(welcome)

        body_layout.addSpacing(20)

        # Info frame
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(10)

        # Email
        email_label = QLabel(f"📧 {self.user.email}")
        email_label.setObjectName("infoLabel")
        email_label.setAlignment(Qt.AlignCenter)
        info_font = QFont("Inter", 11)
        email_label.setFont(info_font)
        info_layout.addWidget(email_label)

        # Role
        role_label = QLabel(f"👤 Rol: {self.user.role.capitalize()}")
        role_label.setObjectName("infoLabel")
        role_label.setAlignment(Qt.AlignCenter)
        role_label.setFont(info_font)
        info_layout.addWidget(role_label)

        body_layout.addWidget(info_frame)

        body_layout.addSpacing(20)

        # Botón cerrar
        close_button = QPushButton("Cerrar")
        close_button.setObjectName("closeButton")
        close_button.setFixedHeight(45)
        button_font = QFont("Inter", 11, QFont.Bold)
        close_button.setFont(button_font)
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.clicked.connect(self.close)
        body_layout.addWidget(close_button)

        body_layout.addStretch()

        card_layout.addWidget(body)
        main_layout.addWidget(card)

    def apply_styles(self):
        """Aplicar estilos CSS"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f4f8;
            }

            QFrame#card {
                background-color: white;
                border-radius: 12px;
            }

            QFrame#successHeader {
                background-color: #10B981;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }

            QFrame#successHeader QLabel {
                color: white;
            }

            QLabel#successTitle {
                color: white;
            }

            QFrame#body {
                background-color: white;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }

            QLabel#welcomeText {
                color: #1F2937;
            }

            QFrame#infoFrame {
                background-color: #F3F4F6;
                border-radius: 8px;
                padding: 15px;
            }

            QLabel#infoLabel {
                color: #6B7280;
            }

            QPushButton#closeButton {
                background-color: #6B7280;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }

            QPushButton#closeButton:hover {
                background-color: #4B5563;
            }

            QPushButton#closeButton:pressed {
                background-color: #374151;
            }
        """)


def main():
    """Función principal"""
    app_qt = QApplication(sys.argv)

    # Configurar fuente por defecto
    app_qt.setFont(QFont("Inter", 10))

    # Crear y mostrar ventana de login
    window = LoginWindow()
    window.show()

    sys.exit(app_qt.exec())


if __name__ == '__main__':
    main()
