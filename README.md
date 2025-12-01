# FAT Testing - Sistema de Pruebas para Dispositivos Cisco

Plataforma web para gestión de pruebas automatizadas en switches Cisco Catalyst con generación de informes.

## Requisitos Previos

- Python 3.8 o superior
- MySQL Server 5.7 o superior

## Instalación

### 1. Extraer el proyecto

Descomprimir el archivo .zip en la ubicación deseada.

### 2. Instalar dependencias de Python

Abrir terminal en la carpeta del proyecto y ejecutar:

```bash
pip install -r requirements.txt
```

### 3. Configurar MySQL

Abrir MySQL y crear la base de datos:

```sql
CREATE DATABASE fat_testing_db;
```

Asegurarse que MySQL esté corriendo en localhost:3306 con usuario `root` y contraseña `1234`.

Si usa credenciales diferentes, modificar la línea 17 de `config.py`:

```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://usuario:contraseña@localhost/fat_testing_db'
```

### 4. Configurar variables de entorno

Crear un archivo llamado `.env` en la raíz del proyecto con el siguiente contenido:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=tu_email@gmail.com
MAIL_PASSWORD=tu_app_password
MAIL_DEFAULT_SENDER=noreply@fat-testing.com
SECRET_KEY=una-clave-secreta-cualquiera
MP_ACCESS_TOKEN=tu_token_mercadopago
PREAPPROVAL_PLAN_ID=tu_plan_id
MP_TEST_PAYER_EMAIL=test@testuser.com
```

Nota: Si no se configuran las credenciales de Mercado Pago o Gmail, esas funcionalidades no estarán disponibles pero la aplicación seguirá funcionando.

## Ejecución

Desde la carpeta del proyecto, ejecutar:

```bash
python __init__.py
```

La aplicación estará disponible en `http://localhost:80`

Para detener el servidor, presionar `Ctrl + C` en la terminal.

## Uso de la Aplicación

1. Abrir navegador en `http://localhost:80`
2. Registrarse con email y contraseña
3. Iniciar sesión con las credenciales creadas
4. Acceder al dashboard para usar las funcionalidades

## Aplicación Desktop

El ejecutable se encuentra en `downloads/FAT_Testing.exe` y puede ejecutarse directamente sin instalación.

## Problemas Comunes

### Error de conexión a MySQL

Verificar que MySQL esté corriendo y que las credenciales sean correctas (por defecto: root/1234).

### Error al instalar dependencias

Si falla la instalación de alguna dependencia, intentar:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Puerto 80 ocupado

Si el puerto 80 está en uso, modificar la línea final de `__init__.py`:

```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

Luego acceder a `http://localhost:5000`

Se adjunta base de datos con usuario ya con cuenta activa

Correo: nicolas.huenchuen.r@gmail.com
contraseña: Hola1234#
