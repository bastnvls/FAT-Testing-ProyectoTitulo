# Características de Seguridad - FAT Testing

## Nuevas Funcionalidades Implementadas

Este documento describe las mejoras de seguridad y autenticación implementadas en el sistema FAT Testing.

---

## 1. Validación de Contraseñas Seguras

### Requisitos de Contraseña

Todas las contraseñas deben cumplir con los siguientes requisitos:

- **Longitud mínima**: 8 caracteres
- **Letra mayúscula**: Al menos una (A-Z)
- **Letra minúscula**: Al menos una (a-z)
- **Número**: Al menos un dígito (0-9)
- **Carácter especial**: Al menos uno (!@#$%^&*(),.?":{}|<>_-+=[]\/;~`)

### Implementación

- Validación en el backend (Python) en `utils.py`
- Validación en el frontend (JavaScript) con feedback en tiempo real
- Indicadores visuales que muestran qué requisitos se cumplen

---

## 2. Validación de Correo Electrónico

### Características

- **Validación de formato**: Usando la librería `email-validator`
- **Normalización**: Los correos se normalizan antes de guardarlos
- **Verificación de duplicados**: No se permiten correos duplicados
- **Validación robusta**: Detecta formatos inválidos y errores comunes

### Ejemplos de Validación

```python
# Válido
usuario@ejemplo.com → usuario@ejemplo.com

# Normalizado
Usuario@Ejemplo.COM → usuario@ejemplo.com

# Inválido
usuario@
@ejemplo.com
usuario.ejemplo.com
```

---

## 3. Verificación de Cuentas Duplicadas

### Validaciones Implementadas

1. **Nombre de usuario**:
   - Mínimo 3 caracteres, máximo 80
   - Validación case-insensitive (Juan = juan = JUAN)
   - No se permiten duplicados

2. **Correo electrónico**:
   - Email normalizado
   - Validación de formato
   - No se permiten duplicados
   - Case-insensitive

### Mensajes de Error

- "El nombre de usuario ya está en uso"
- "El correo electrónico ya está registrado"

---

## 4. Sistema de Recuperación de Contraseña

### Flujo Completo

#### Paso 1: Solicitar Recuperación

1. Usuario hace clic en "¿Olvidaste tu contraseña?" en el login
2. Ingresa su correo electrónico
3. Sistema valida el formato del correo
4. Si el correo existe, se genera un token único
5. Se envía un correo con instrucciones

#### Paso 2: Recibir Correo

El correo incluye:
- Enlace único de recuperación
- Tiempo de expiración (1 hora)
- Instrucciones claras
- Diseño profesional en HTML

#### Paso 3: Restablecer Contraseña

1. Usuario hace clic en el enlace del correo
2. Sistema valida que el token sea válido y no haya expirado
3. Usuario ingresa nueva contraseña
4. Se validan los requisitos de seguridad
5. Contraseña se actualiza
6. Token se marca como usado
7. Usuario puede iniciar sesión con la nueva contraseña

### Seguridad del Sistema

- **Tokens únicos**: Generados con `secrets.token_urlsafe(32)`
- **Expiración**: Tokens válidos por 1 hora
- **Uso único**: Cada token solo puede usarse una vez
- **Invalidación automática**: Tokens anteriores se invalidan al solicitar uno nuevo
- **Protección contra enumeración**: Mensaje genérico aunque el email no exista

---

## 5. Configuración de Correo Electrónico

### Archivo .env

Crea un archivo `.env` en la raíz del proyecto:

```bash
# Servidor SMTP
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true

# Credenciales
MAIL_USERNAME=tu-correo@gmail.com
MAIL_PASSWORD=tu-contraseña-de-aplicacion

# Remitente
MAIL_DEFAULT_SENDER=noreply@fat-testing.com
```

### Configuración para Gmail

1. Activa la verificación en dos pasos en tu cuenta de Google
2. Ve a: https://myaccount.google.com/apppasswords
3. Genera una "Contraseña de aplicación"
4. Usa esa contraseña en `MAIL_PASSWORD`

### Configuración para Outlook

```bash
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=tu-correo@outlook.com
MAIL_PASSWORD=tu-contraseña-normal
```

---

## 6. Nuevas Rutas de la Aplicación

### Rutas Públicas

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/forgot-password` | GET, POST | Solicitar recuperación de contraseña |
| `/reset-password/<token>` | GET, POST | Restablecer contraseña con token |

### Ejemplo de Uso

```
1. Login: https://localhost/login
2. Olvidé contraseña: https://localhost/forgot-password
3. Reset (desde correo): https://localhost/reset-password/abc123xyz...
```

---

## 7. Base de Datos

### Nueva Tabla: password_reset_tokens

```sql
CREATE TABLE password_reset_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(100) UNIQUE NOT NULL,
    created_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX (token)
);
```

### Migración

Ejecuta el script de migración para crear la nueva tabla:

```bash
python migrate_db.py
```

---

## 8. Archivos Modificados y Creados

### Archivos Modificados

1. **`requirements.txt`** - Agregado Flask-Mail
2. **`config.py`** - Configuración de correo y políticas de contraseña
3. **`models.py`** - Nuevo modelo PasswordResetToken
4. **`__init__.py`** - Rutas de recuperación y validaciones mejoradas
5. **`templates/login.html`** - Link de recuperación de contraseña
6. **`templates/register.html`** - Requisitos de contraseña visuales

### Archivos Creados

1. **`utils.py`** - Funciones de validación y envío de correos
2. **`templates/forgot_password.html`** - Formulario de recuperación
3. **`templates/reset_password.html`** - Formulario de nueva contraseña
4. **`.env.example`** - Plantilla de variables de entorno
5. **`migrate_db.py`** - Script de migración de base de datos
6. **`SECURITY_FEATURES.md`** - Esta documentación

---

## 9. Instalación y Configuración

### Paso 1: Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Paso 2: Configurar Variables de Entorno

```bash
# Copia el archivo de ejemplo
cp .env.example .env

# Edita .env con tus credenciales
notepad .env  # Windows
nano .env     # Linux/Mac
```

### Paso 3: Migrar Base de Datos

```bash
python migrate_db.py
```

### Paso 4: Iniciar Aplicación

```bash
python __init__.py
```

---

## 10. Pruebas Recomendadas

### Prueba 1: Registro con Contraseña Débil

1. Intenta registrarte con contraseña "123456"
2. Deberías ver un error: "La contraseña debe contener..."

### Prueba 2: Correo Duplicado

1. Regístrate con un correo
2. Intenta registrarte nuevamente con el mismo correo
3. Deberías ver: "El correo electrónico ya está registrado"

### Prueba 3: Recuperación de Contraseña

1. Ve a /login
2. Haz clic en "¿Olvidaste tu contraseña?"
3. Ingresa tu correo
4. Revisa tu bandeja de entrada
5. Haz clic en el enlace del correo
6. Establece una nueva contraseña
7. Inicia sesión con la nueva contraseña

### Prueba 4: Token Expirado

1. Solicita recuperación de contraseña
2. Espera más de 1 hora
3. Intenta usar el enlace
4. Deberías ver: "El enlace de recuperación es inválido o ha expirado"

---

## 11. Mejores Prácticas de Seguridad

### Para Desarrollo

- Usa variables de entorno para credenciales
- No compartas el archivo `.env`
- Genera contraseñas de aplicación para Gmail
- Prueba el envío de correos en local

### Para Producción

- Cambia `SECRET_KEY` a una clave aleatoria fuerte
- Usa HTTPS (cambia `SESSION_COOKIE_SECURE = True`)
- Considera usar un servicio de email dedicado (SendGrid, Amazon SES)
- Implementa rate limiting para prevenir spam
- Monitorea los intentos fallidos de login

---

## 12. Solución de Problemas

### Error: "No se pudo enviar el correo"

**Causa**: Credenciales SMTP incorrectas

**Solución**:
1. Verifica que `MAIL_USERNAME` y `MAIL_PASSWORD` sean correctos
2. Para Gmail, usa una contraseña de aplicación
3. Verifica que la verificación en dos pasos esté activada (Gmail)

### Error: "El enlace ha expirado"

**Causa**: Token expirado (más de 1 hora)

**Solución**:
1. Solicita un nuevo enlace de recuperación
2. Usa el enlace dentro de 1 hora

### Error: "Correo inválido"

**Causa**: Formato de email incorrecto

**Solución**:
1. Verifica que el formato sea `usuario@dominio.com`
2. No uses espacios ni caracteres especiales inválidos

---

## 13. Contacto y Soporte

Si encuentras algún problema o tienes sugerencias, por favor reporta en el repositorio del proyecto.

---

**Versión**: 2.0
**Fecha**: 2025
**Autor**: FAT Testing Team
