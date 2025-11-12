import os

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
