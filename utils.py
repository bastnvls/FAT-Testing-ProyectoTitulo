"""
Utilidades de validación y envío de correos
"""
import re
from flask import url_for, render_template_string


def validate_email_format(email):
    """
    Valida el formato del correo electrónico

    Returns:
        tuple: (is_valid, normalized_email, error_message)
    """
    if not email:
        return False, None, "El correo electrónico es requerido"

    # Normalizar: convertir a minúsculas y eliminar espacios
    normalized_email = email.lower().strip()

    # Patrón RFC 5322 simplificado para validar correos
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_pattern, normalized_email):
        return False, None, "Formato de correo electrónico inválido"

    # Validar longitud
    if len(normalized_email) > 254:
        return False, None, "El correo electrónico es demasiado largo"

    return True, normalized_email, None


def validate_password_strength(password):
    """
    Valida la fortaleza de la contraseña

    Requisitos:
    - Mínimo 8 caracteres
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número

    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "La contraseña es requerida"

    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"

    if len(password) > 128:
        return False, "La contraseña es demasiado larga (máximo 128 caracteres)"

    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe contener al menos una letra mayúscula"

    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe contener al menos una letra minúscula"

    if not re.search(r'\d', password):
        return False, "La contraseña debe contener al menos un número"

    return True, None


def send_password_reset_email(user, token, mail):
    """
    Envía correo de recuperación de contraseña

    Args:
        user: Objeto User
        token: Token de recuperación
        mail: Objeto Flask-Mail

    Returns:
        bool: True si se envió exitosamente, False si hubo error
    """
    try:
        from flask_mail import Message
        from flask import current_app

        # Generar URL de reseteo
        reset_url = url_for('reset_password', token=token, _external=True)

        # Template del correo
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Inter', Arial, sans-serif;
                    background-color: #f8fafc;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
                    padding: 40px 30px;
                    text-align: center;
                    color: white;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .content h2 {{
                    color: #1e293b;
                    font-size: 24px;
                    margin-bottom: 16px;
                }}
                .content p {{
                    color: #64748b;
                    font-size: 16px;
                    line-height: 1.6;
                    margin-bottom: 16px;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
                    color: white;
                    padding: 16px 32px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    margin: 24px 0;
                }}
                .footer {{
                    background-color: #f8fafc;
                    padding: 24px 30px;
                    text-align: center;
                    color: #94a3b8;
                    font-size: 14px;
                }}
                .warning {{
                    background-color: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 16px;
                    margin: 24px 0;
                    border-radius: 4px;
                }}
                .warning p {{
                    margin: 0;
                    color: #92400e;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 FAT Testing</h1>
                </div>
                <div class="content">
                    <h2>Recuperación de Contraseña</h2>
                    <p>Hola <strong>{user.username}</strong>,</p>
                    <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en FAT Testing.</p>
                    <p>Para crear una nueva contraseña, haz clic en el siguiente botón:</p>
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">Restablecer Contraseña</a>
                    </div>
                    <div class="warning">
                        <p><strong>⏰ Este enlace expirará en 1 hora</strong></p>
                    </div>
                    <p>Si no solicitaste este cambio, puedes ignorar este correo de forma segura. Tu contraseña actual permanecerá sin cambios.</p>
                    <p style="color: #94a3b8; font-size: 14px; margin-top: 32px;">
                        Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
                        <a href="{reset_url}" style="color: #2563eb; word-break: break-all;">{reset_url}</a>
                    </p>
                </div>
                <div class="footer">
                    <p>© 2025 FAT Testing. Todos los derechos reservados.</p>
                    <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Recuperación de Contraseña - FAT Testing

        Hola {user.username},

        Recibimos una solicitud para restablecer la contraseña de tu cuenta.

        Para crear una nueva contraseña, visita el siguiente enlace:
        {reset_url}

        Este enlace expirará en 1 hora.

        Si no solicitaste este cambio, puedes ignorar este correo de forma segura.

        Saludos,
        Equipo de FAT Testing
        """

        msg = Message(
            subject='Recuperación de Contraseña - FAT Testing',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        return True

    except Exception as e:
        print(f"Error al enviar correo: {str(e)}")
        return False
