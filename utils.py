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
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

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

    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe contener al menos una letra mayúscula"

    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe contener al menos una letra minúscula"

    if not re.search(r"\d", password):
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
        reset_url = url_for("reset_password", token=token, _external=True)

        # Obtener nombre para mostrar (como en el segundo código)
        display_name = (
            f"{(user.nombre or '').strip()} {(user.apellido or '').strip()}".strip()
            or user.username
            or user.email
        )

        # Template del correo mejorado
        html_body = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8" />
            <style>
                body {{
                    font-family: 'Inter', Arial, sans-serif;
                    background-color: #e5e7eb;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    width: 100%;
                    background: #e5e7eb;
                    padding: 24px 0;
                }}
                .wrapper {{
                    max-width: 640px;
                    margin: 0 auto;
                    background-color: white;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.08);
                }}
                .hero {{
                    background: linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%);
                    color: #fff;
                    padding: 28px 32px 36px;
                    text-align: center;
                }}
                .hero h1 {{
                    margin: 0;
                    font-size: 26px;
                    font-weight: 700;
                }}
                .hero p {{
                    margin: 6px 0 0;
                    font-size: 13px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 32px 36px 36px;
                    font-size: 15px;
                    line-height: 1.6;
                }}
                .content h2 {{
                    color: #1e293b;
                    font-size: 24px;
                    margin-bottom: 16px;
                }}
                .content p {{
                    color: #1f2937;
                    font-size: 15px;
                    line-height: 1.6;
                    margin-bottom: 16px;
                }}
                .button {{
                    display: inline-block;
                    margin: 22px 0;
                    padding: 14px 26px;
                    background: linear-gradient(135deg, #2563eb 0%, #4338ca 100%);
                    color: #fff !important;
                    text-decoration: none;
                    border-radius: 10px;
                    font-weight: 600;
                    font-size: 15px;
                    box-shadow: 0 10px 22px rgba(67, 56, 202, 0.25);
                }}
                .footer {{
                    text-align: center;
                    color: #6b7280;
                    font-size: 12px;
                    padding: 18px;
                    background: #f9fafb;
                }}
                .warning {{
                    margin: 20px 0;
                    padding: 12px 14px;
                    border-left: 4px solid #f59e0b;
                    background: #fff7e6;
                    color: #92400e;
                    border-radius: 10px;
                    font-size: 14px;
                }}
                .warning p {{
                    margin: 0;
                    color: #92400e;
                }}
                .link {{
                    color: #2563eb;
                    word-break: break-all;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="wrapper">
                    <div class="hero">
                        <h1>🔐 Recuperación de Contraseña</h1>
                        <p>FAT Testing</p>
                    </div>
                    <div class="content">
                        <p>Hola <strong>{display_name}</strong>,</p>
                        <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en FAT Testing.</p>
                        <p>Para crear una nueva contraseña, haz clic en el siguiente botón:</p>
                        <div style="text-align: center;">
                            <a href="{reset_url}" class="button">Restablecer Contraseña</a>
                        </div>
                        <div class="warning">
                            <p><strong>⏰ Importante:</strong> Este enlace expirará en 1 hora por razones de seguridad.</p>
                        </div>
                        <p>Si no solicitaste este cambio, puedes ignorar este correo de forma segura. Tu contraseña actual permanecerá sin cambios.</p>
                        <p style="color: #6b7280; font-size: 14px; margin-top: 32px;">
                            Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
                            <a href="{reset_url}" class="link">{reset_url}</a>
                        </p>
                    </div>
                    <div class="footer">
                        © 2025 FAT Testing. Todos los derechos reservados.<br/>
                        Este es un correo automático, por favor no respondas a este mensaje.
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Recuperación de Contraseña - FAT Testing

        Hola {display_name},

        Hemos recibido una solicitud para restablecer la contraseña de tu cuenta.

        Para crear una nueva contraseña, visita el siguiente enlace:
        {reset_url}

        Este enlace expirará en 1 hora por razones de seguridad.

        Si no solicitaste este cambio, puedes ignorar este correo de forma segura.

        Saludos,
        Equipo de FAT Testing
        """

        msg = Message(
            subject="Recuperación de Contraseña - FAT Testing",
            sender=current_app.config["MAIL_DEFAULT_SENDER"],
            recipients=[user.email],
            body=text_body,
            html=html_body,
        )

        mail.send(msg)
        return True

    except Exception as e:
        print(f"Error al enviar correo: {str(e)}")
        return False
