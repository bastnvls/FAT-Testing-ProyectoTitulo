from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import secrets

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    """Modelo de usuario para autenticación y autorización"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'user' o 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __init__(self, username, email, password, role='user'):
        """Inicializar usuario con contraseña hasheada"""
        self.username = username
        self.email = email
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.role = role

    def check_password(self, password):
        """Verificar si la contraseña es correcta"""
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Verificar si el usuario es administrador"""
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'


class PasswordResetToken(db.Model):
    """Modelo para tokens de restablecimiento de contraseña"""

    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

    # Relación con el usuario
    user = db.relationship('User', backref=db.backref('reset_tokens', lazy=True))

    def __init__(self, user_id, expiration_hours=1):
        """
        Inicializar token de restablecimiento de contraseña

        Args:
            user_id (int): ID del usuario
            expiration_hours (int): Horas hasta que expire el token (default: 1)
        """
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(hours=expiration_hours)

    def is_valid(self):
        """
        Verificar si el token es válido

        Returns:
            bool: True si el token no ha expirado y no ha sido usado
        """
        return not self.used and datetime.utcnow() < self.expires_at

    def mark_as_used(self):
        """Marcar el token como usado"""
        self.used = True

    @staticmethod
    def get_valid_token(token_string):
        """
        Obtener un token válido por su string

        Args:
            token_string (str): String del token

        Returns:
            PasswordResetToken o None: Token si es válido, None si no existe o expiró
        """
        token = PasswordResetToken.query.filter_by(token=token_string).first()
        if token and token.is_valid():
            return token
        return None

    def __repr__(self):
        return f'<PasswordResetToken {self.token[:8]}... for User {self.user_id}>'
