from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import secrets

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    """
    Propósito:
        Representa la tabla de usuarios con la info de acceso, datos básicos y estado de suscripción.
    Dependencias:
        - db (SQLAlchemy) para mapear la tabla.
        - bcrypt para generar y validar hashes de contraseña.
        - UserMixin para compatibilidad con Flask-Login.
    """

    __tablename__ = 'usuarios'

    # Clave primaria incremental (sencilla de usar y referenciar)
    id = db.Column(db.Integer, primary_key=True)

    # Correo único: credencial principal de login
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)

    # Hash de la contraseña (nunca se guarda en texto plano)
    password_hash = db.Column(db.String(255), nullable=False)

    # Datos básicos opcionales
    nombre = db.Column(db.String(80))
    apellido = db.Column(db.String(80))

    # Estado lógico de la cuenta: ACTIVA/BLOQUEADA/PENDIENTE_VERIFICACION
    estado_cuenta = db.Column(db.String(20), default='ACTIVA', nullable=False)

    # Estado de la suscripción: ACTIVA/VENCIDA/EN_GRACIA/SIN_SUSCRIPCION
    estado_suscripcion = db.Column(db.String(20), default='SIN_SUSCRIPCION', nullable=False)

    # Fechas asociadas a suscripción/bloqueo
    fecha_fin_suscripcion = db.Column(db.Date)
    fecha_bloqueo = db.Column(db.Date)

    # ID de suscripción recurrente en Mercado Pago (si aplica)
    mp_preapproval_id = db.Column(db.String(100))

    # Tiempos de auditoría
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ultimo_acceso = db.Column(db.DateTime)

    def __init__(self, email, password, nombre=None, apellido=None):
        """Entradas: email (str), password (str), nombre (str opcional), apellido (str opcional)"""
        self.email = email
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.nombre = nombre
        self.apellido = apellido

    def check_password(self, password):
        """Propósito: validar contraseña comparando contra el hash almacenado."""
        return bcrypt.check_password_hash(self.password_hash, password)

class PasswordResetToken(db.Model):
    """
    Propósito:
        Gestiona tokens de recuperación de contraseña con expiración y flag de uso.
    Dependencias:
        - secrets para generar tokens seguros.
        - datetime/timedelta para calcular expiración.
    """

    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    # FK a usuarios.id (Integer porque el modelo usa IDs enteros)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # Token único para el enlace de recuperación
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)

    # Auditoría y expiración
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

    # Relación hacia el usuario (permite token.user)
    user = db.relationship('User', backref=db.backref('reset_tokens', lazy=True))

    def __init__(self, user_id, expiration_hours=1):
        """Entradas: user_id (int), expiration_hours (int, por defecto 1 hora)."""
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(hours=expiration_hours)

    def is_valid(self):
        """Propósito: saber si el token sigue vigente (no usado y no expirado)."""
        return not self.used and datetime.utcnow() < self.expires_at

    def mark_as_used(self):
        """Propósito: marcar el token como consumido para invalidarlo."""
        self.used = True

    @staticmethod
    def get_valid_token(token_string):
        """
        Entradas: token_string (str).
        Salidas: instancia PasswordResetToken válida o None.
        Propósito: obtener un token solo si existe y pasa las validaciones.
        """
        token = PasswordResetToken.query.filter_by(token=token_string).first()
        if token and token.is_valid():
            return token
        return None

    def __repr__(self):
        return f'<PasswordResetToken {self.token[:8]}... for User {self.user_id}>'
