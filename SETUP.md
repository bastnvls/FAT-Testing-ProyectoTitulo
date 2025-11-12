# FAT Testing 2.0 - Guía de Configuración

## Descripción

FAT Testing 2.0 es una aplicación web para automatizar pruebas de aceptación de fábrica (Factory Acceptance Test) en dispositivos de red. La aplicación incluye:

- Sistema de autenticación de usuarios con roles (admin/usuario)
- Procesamiento automático de archivos de configuración
- Generación de informes Word profesionales
- Landing page con información del proyecto
- Dashboard de administración

## Requisitos Previos

- Python 3.8 o superior
- MySQL Server 5.7 o superior
- pip (gestor de paquetes de Python)

## Instalación

### 1. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar MySQL

Crea una base de datos en MySQL:

```sql
CREATE DATABASE fat_testing_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Crea un usuario (opcional pero recomendado):

```sql
CREATE USER 'fat_user'@'localhost' IDENTIFIED BY 'tu_contraseña';
GRANT ALL PRIVILEGES ON fat_testing_db.* TO 'fat_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto (opcional):

```env
SECRET_KEY=tu-clave-secreta-super-segura-aqui
DATABASE_URL=mysql+pymysql://fat_user:tu_contraseña@localhost/fat_testing_db
```

O modifica directamente el archivo `config.py`:

```python
# En config.py, línea 7-8
SECRET_KEY = 'tu-clave-secreta'
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://usuario:contraseña@localhost/fat_testing_db'
```

### 4. Inicializar la base de datos

La base de datos se inicializa automáticamente al ejecutar la aplicación, pero también puedes hacerlo manualmente:

```bash
flask init-db
```

### 5. Crear usuario administrador

Hay dos formas de crear un usuario administrador:

**Opción A: Usando comando Flask**
```bash
flask create-admin
```

**Opción B: Directamente desde Python**
```python
from models import db, User
from __init__ import app

with app.app_context():
    admin = User(username='admin', email='admin@example.com', password='admin123', role='admin')
    db.session.add(admin)
    db.session.commit()
```

## Ejecución

### Modo de desarrollo

```bash
python __init__.py
```

La aplicación estará disponible en: `http://localhost:80`

**Nota**: En Windows, es posible que necesites permisos de administrador para usar el puerto 80.

### Modo de producción

Para producción, se recomienda usar un servidor WSGI como Gunicorn:

```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:80 __init__:app
```

## Uso de la Aplicación

### 1. Landing Page

- Accede a `http://localhost:80/` para ver el landing page
- Contiene información del proyecto y botón de suscripción (no funcional aún)
- Enlaces para registrarse e iniciar sesión

### 2. Registro de Usuario

- Haz clic en "Registrarse" en el landing page
- Completa el formulario con:
  - Nombre de usuario (mínimo 3 caracteres)
  - Correo electrónico
  - Contraseña (mínimo 6 caracteres)
  - Confirmar contraseña
- Los usuarios nuevos tienen rol "user" por defecto

### 3. Inicio de Sesión

- Haz clic en "Iniciar Sesión"
- Ingresa tu correo y contraseña
- Opcionalmente, marca "Recordarme" para mantener la sesión activa

### 4. Procesamiento de Archivos FAT

Una vez autenticado:

1. Selecciona el tipo de dispositivo
2. Sube el archivo de configuración (.txt)
3. Agrega las imágenes de las pruebas FAT
4. Completa la información del proyecto
5. Haz clic en "Procesar"
6. Descarga el informe Word generado

### 5. Dashboard de Administrador

Los usuarios con rol "admin" tienen acceso al dashboard:

- Accede desde el botón "Dashboard" en la barra superior
- Visualiza estadísticas de usuarios
- Ve la lista completa de usuarios registrados
- Consulta información como ID, email, rol, estado y fecha de registro

## Estructura del Proyecto

```
FAT-Testing-2.0/
├── __init__.py              # Aplicación principal Flask
├── models.py                # Modelos de base de datos
├── config.py                # Configuración de la aplicación
├── requirements.txt         # Dependencias del proyecto
├── templates/               # Plantillas HTML
│   ├── landing.html        # Landing page
│   ├── login.html          # Página de login
│   ├── register.html       # Página de registro
│   ├── dashboard.html      # Dashboard admin
│   └── index.html          # Aplicación principal
├── static/                  # Archivos estáticos
│   ├── styles.css
│   ├── scripts.js
│   └── GlobalLogo_NTTDATA_FutureBlue_RGB.png
├── plantillas/              # Plantillas de Word
└── funcionalidades/         # Módulos de funcionalidades
    ├── resaltado.py
    ├── colores.py
    └── modelos/             # Modelos de dispositivos
```

## Solución de Problemas

### Error de conexión a MySQL

Si recibes un error de conexión a MySQL:

1. Verifica que MySQL esté ejecutándose
2. Confirma las credenciales en `config.py`
3. Asegúrate de que la base de datos existe
4. Verifica que PyMySQL esté instalado: `pip install PyMySQL`

### Error de puerto 80 en uso

Si el puerto 80 ya está en uso, modifica la línea final de `__init__.py`:

```python
app.run(host="0.0.0.0", port=5000, debug=True)  # Cambiar 80 a 5000
```

### Error de permisos en Windows

En Windows, necesitas ejecutar como administrador para usar el puerto 80, o cambia a otro puerto (5000, 8080, etc.).

## Seguridad

Para producción, asegúrate de:

1. Cambiar `SECRET_KEY` en `config.py` a un valor aleatorio y seguro
2. Usar contraseñas fuertes para la base de datos
3. Activar HTTPS configurando `SESSION_COOKIE_SECURE = True`
4. Configurar un firewall para proteger MySQL
5. Deshabilitar el modo debug: `debug=False`

## Soporte de Dispositivos

La aplicación soporta los siguientes dispositivos:

- **Access Points**: C9115AXI, C9120AXE, C9130AXI
- **Switches L2**: 9200, 9300, 9500
- **Switches L3**: 9348GC, C93180YC
- **Switches Industriales**: IE3300, IE4010
- **Routers**: C8500, ISR4431
- **Firewalls**: CheckPoint 6200, CheckPoint 6600

## Contribución

Para contribuir al proyecto:

1. Crea una rama para tu feature
2. Realiza tus cambios
3. Haz commit con mensajes descriptivos
4. Crea un pull request

## Licencia

© 2025 FAT Testing App - NTT DATA. Todos los derechos reservados.
