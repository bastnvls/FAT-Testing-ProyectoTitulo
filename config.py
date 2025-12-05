import os
from dotenv import load_dotenv
import mercadopago
from datetime import timedelta

load_dotenv()

class Config:
    """Configuración base de la aplicación"""

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # BASE DE DATOS
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:1234@localhost/fat_testing_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SEGURIDAD DE SESIÓN Y COOKIES
    SESSION_PERMANENT = False  # La sesión muere al cerrar navegador
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Esto en True cuando se usa HTTPS (producción)
    SESSION_COOKIE_SECURE = False 

    # SEGURIDAD CSRF (Flask-WTF) 
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hora

    # Configuración Flask-Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@fat-testing.com'

    # Configuración Passwords
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGITS = True
    PASSWORD_REQUIRE_SPECIAL = True

    # Configuración de carga de archivos
    # Límite total de tamaño de request (incluye todos los archivos del formulario)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB total (logs de router pueden ser extensos)

    # Límites específicos por tipo de archivo (en bytes)
    MAX_FILE_SIZE_TXT = 20 * 1024 * 1024  # 20 MB para archivos .txt (logs de consola Cisco)
    MAX_FILE_SIZE_IMAGE = 5 * 1024 * 1024  # 5 MB por imagen (JPG/PNG optimizado)

    # MercadoPago
    sdk_mp = mercadopago.SDK(os.environ["MP_ACCESS_TOKEN"])
    MP_WEBHOOK_SECRET = os.environ.get('MP_WEBHOOK_SECRET')