from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta, timezone 
import secrets
import uuid 

db = SQLAlchemy()
bcrypt = Bcrypt()


def get_now_utc():
    return datetime.now(timezone.utc)

class User(db.Model, UserMixin):
    """
    Propósito:
        Representa la tabla de usuarios con la info de acceso, datos básicos y estado de suscripción.
    """

    __tablename__ = 'usuarios'

    # Clave primaria UUID
    id_usuario = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Correo único
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)

    # Hash de la contraseña
    password_hash = db.Column(db.String(255), nullable=False)

    # Datos básicos
    nombre = db.Column(db.String(80))
    apellido = db.Column(db.String(80))

    # Estado lógico de la cuenta
    estado_cuenta = db.Column(db.String(20), default='ACTIVA', nullable=False)

    # Estado de la suscripción
    estado_suscripcion = db.Column(db.String(20), default='SIN_SUSCRIPCION', nullable=False)

    # Fechas asociadas a suscripción (OJO: db.Date solo guarda AAAA-MM-DD)
    fecha_fin_suscripcion = db.Column(db.Date)

    # ID de suscripción en Mercado Pago
    mp_preapproval_id = db.Column(db.String(100))

    # Tiempos de auditoría / licencias
    licencia_valida_hasta = db.Column(db.DateTime)
    
    # Uso de la función auxiliar para UTC
    fecha_creacion = db.Column(db.DateTime, default=get_now_utc, nullable=False)
    ultimo_acceso = db.Column(db.DateTime)

    def __init__(self, email, password, nombre=None, apellido=None):
        self.email = email
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.nombre = nombre
        self.apellido = apellido
        # Aseguramos fecha creación al instanciar
        self.fecha_creacion = get_now_utc()

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id_usuario)


class PasswordResetToken(db.Model):
    """
    Propósito:
        Gestiona tokens de recuperación de contraseña.
    """

    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.String(36),
        db.ForeignKey('usuarios.id_usuario'),
        nullable=False,
        index=True
    )

    token = db.Column(db.String(100), unique=True, nullable=False, index=True)

    # Uso de la función auxiliar para UTC
    created_at = db.Column(db.DateTime, default=get_now_utc, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship('User', backref=db.backref('reset_tokens', lazy=True))

    def __init__(self, user_id, expiration_hours=1):
        self.user_id = str(user_id)
        self.token = secrets.token_urlsafe(32)
        # Cálculo con timezone
        self.expires_at = get_now_utc() + timedelta(hours=expiration_hours)
        self.created_at = get_now_utc()

    def is_valid(self):
        # Comparación con timezone aware
        return not self.used and get_now_utc() < self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else get_now_utc() < self.expires_at

    def mark_as_used(self):
        self.used = True

    @staticmethod
    def get_valid_token(token_string):
        token = PasswordResetToken.query.filter_by(token=token_string).first()
        if token and token.is_valid():
            return token
        return None

    def __repr__(self):
        return f'<PasswordResetToken {self.token[:8]}... for User {self.user_id}>'