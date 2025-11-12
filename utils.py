"""
Utilidades para validación de datos y envío de correos
"""
import re
from email_validator import validate_email, EmailNotValidError
from flask_mail import Message
from flask import current_app, url_for


def validate_password_strength(password):
    """
    Valida que la contraseña cumpla con los requisitos de seguridad.

    Args:
        password (str): Contraseña a validar

    Returns:
        tuple: (bool, str) - (es_valida, mensaje_error)
    """
    config = current_app.config

    # Validar longitud mínima
    min_length = config.get('PASSWORD_MIN_LENGTH', 8)
    if len(password) < min_length:
        return False, f'La contraseña debe tener al menos {min_length} caracteres'

    # Validar mayúsculas
    if config.get('PASSWORD_REQUIRE_UPPERCASE', True):
        if not re.search(r'[A-Z]', password):
            return False, 'La contraseña debe contener al menos una letra mayúscula'

    # Validar minúsculas
    if config.get('PASSWORD_REQUIRE_LOWERCASE', True):
        if not re.search(r'[a-z]', password):
            return False, 'La contraseña debe contener al menos una letra minúscula'

    # Validar dígitos
    if config.get('PASSWORD_REQUIRE_DIGITS', True):
        if not re.search(r'\d', password):
            return False, 'La contraseña debe contener al menos un número'

    # Validar caracteres especiales
    if config.get('PASSWORD_REQUIRE_SPECIAL', True):
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;~`]', password):
            return False, 'La contraseña debe contener al menos un carácter especial (!@#$%^&*...)'

    return True, 'Contraseña válida'


def validate_email_format(email):
    """
    Valida el formato del correo electrónico usando email-validator.

    Args:
        email (str): Correo electrónico a validar

    Returns:
        tuple: (bool, str, str) - (es_valido, email_normalizado, mensaje_error)
    """
    try:
        # Validar y normalizar el email
        valid = validate_email(email, check_deliverability=False)
        return True, valid.normalized, None
    except EmailNotValidError as e:
        return False, None, str(e)


def send_password_reset_email(user, token, mail):
    """
    Envía un correo electrónico con el enlace para restablecer la contraseña.

    Args:
        user: Objeto User
        token (str): Token de restablecimiento de contraseña
        mail: Instancia de Flask-Mail
    """
    reset_url = url_for('reset_password', token=token, _external=True)

    subject = 'Recuperación de Contraseña - FAT Testing'

    # Cuerpo del correo en HTML
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .header {{
                background-color: #0066cc;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }}
            .content {{
                background-color: white;
                padding: 30px;
                border-radius: 0 0 5px 5px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background-color: #0066cc;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 20px;
                font-size: 12px;
                color: #666;
            }}
            .warning {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 10px;
                margin: 15px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Recuperación de Contraseña</h1>
            </div>
            <div class="content">
                <p>Hola <strong>{user.username}</strong>,</p>

                <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en FAT Testing.</p>

                <p>Para crear una nueva contraseña, haz clic en el siguiente botón:</p>

                <center>
                    <a href="{reset_url}" class="button" style="color: white !important;">Restablecer Contraseña</a>
                </center>

                <p>O copia y pega el siguiente enlace en tu navegador:</p>
                <p style="word-break: break-all; color: #0066cc;">{reset_url}</p>

                <div class="warning">
                    <strong>Importante:</strong> Este enlace expirará en 1 hora por razones de seguridad.
                </div>

                <p>Si no solicitaste restablecer tu contraseña, puedes ignorar este correo de forma segura. Tu contraseña actual seguirá siendo válida.</p>

                <p>Saludos,<br>
                El equipo de FAT Testing</p>
            </div>
            <div class="footer">
                <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Cuerpo del correo en texto plano (fallback)
    text_body = f"""
    Recuperación de Contraseña - FAT Testing

    Hola {user.username},

    Hemos recibido una solicitud para restablecer la contraseña de tu cuenta.

    Para crear una nueva contraseña, copia y pega el siguiente enlace en tu navegador:
    {reset_url}

    IMPORTANTE: Este enlace expirará en 1 hora por razones de seguridad.

    Si no solicitaste restablecer tu contraseña, puedes ignorar este correo de forma segura.

    Saludos,
    El equipo de FAT Testing

    ---
    Este es un correo automático, por favor no respondas a este mensaje.
    """

    # Crear y enviar el mensaje
    msg = Message(
        subject=subject,
        recipients=[user.email],
        body=text_body,
        html=html_body
    )

    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False
