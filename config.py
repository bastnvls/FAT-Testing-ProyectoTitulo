import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class Config:
    """Configuración base de la aplicación"""

    # Clave secreta para sesiones (cambiar en producción)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Configuración de la base de datos MySQL
    # Formato: mysql+pymysql://usuario:contraseña@host:puerto/nombre_db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:1234@localhost/fat_testing_db'

    # Desactivar señales de modificación para mejorar rendimiento
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de Flask-Login
    REMEMBER_COOKIE_DURATION = 3600  # 1 hora
    SESSION_COOKIE_SECURE = False  # Cambiar a True en producción con HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Configuración de Flask-Mail para envío de correos
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@fat-testing.com'

    # Configuración de seguridad de contraseñas
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGITS = True
    PASSWORD_REQUIRE_SPECIAL = True
