# Aplicación de Escritorio - FAT Testing

## Descripción

Aplicación de escritorio desarrollada con **PySide6** (Qt para Python) que permite a los usuarios iniciar sesión usando las mismas credenciales de la aplicación web. Se conecta a la misma base de datos MySQL.

---

## Características

- ✅ **Interfaz moderna** con PySide6/Qt
- ✅ **Estilos unificados** con la aplicación web (colores, tipografía)
- ✅ **Conexión a la misma base de datos** MySQL
- ✅ **Autenticación segura** con contraseñas encriptadas
- ✅ **Mensaje de bienvenida personalizado** con información del usuario
- ✅ **Ejecutable independiente** (.exe) sin necesidad de Python instalado

---

## Tecnologías Utilizadas

- **PySide6** 6.6.1 - Framework de interfaz gráfica (Qt)
- **Flask-SQLAlchemy** - ORM para base de datos
- **Flask-Bcrypt** - Encriptación de contraseñas
- **PyMySQL** - Conector MySQL
- **PyInstaller** - Compilación a ejecutable

---

## Requisitos para Desarrollo

### Python y Dependencias

```bash
# Python 3.8 o superior
python --version

# Instalar dependencias
pip install -r requirements.txt
```

### Base de Datos

- MySQL 5.7+ en ejecución
- Base de datos `fat_testing_db` configurada
- Tabla `users` con datos de usuarios

---

## Ejecutar en Modo Desarrollo

```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Ejecutar aplicación
python desktop_app.py
```

---

## Compilar a Ejecutable (.exe)

### Opción 1: Script Automático (Windows)

```bash
# Ejecutar el archivo batch
build_exe.bat
```

Este script:
1. Activa el entorno virtual
2. Instala dependencias necesarias
3. Compila con PyInstaller
4. Genera el ejecutable en `dist/FAT_Testing.exe`

### Opción 2: Script Python

```bash
# Activar entorno virtual
venv\Scripts\activate

# Ejecutar script de compilación
python build_exe.py
```

### Opción 3: PyInstaller Manual

```bash
pyinstaller ^
    --name=FAT_Testing ^
    --onefile ^
    --windowed ^
    --clean ^
    --hidden-import=PySide6 ^
    --hidden-import=flask ^
    --hidden-import=flask_sqlalchemy ^
    --hidden-import=pymysql ^
    desktop_app.py
```

### Resultado

El ejecutable compilado estará en:
```
dist/FAT_Testing.exe
```

**Tamaño aproximado**: 30-50 MB

---

## Distribuir la Aplicación

### Paso 1: Compilar el Ejecutable

Sigue los pasos de la sección anterior para generar `FAT_Testing.exe`

### Paso 2: Mover a Carpeta de Descargas

```bash
# Copiar el ejecutable a la carpeta downloads
copy dist\FAT_Testing.exe downloads\FAT_Testing.exe
```

### Paso 3: Descargar desde la Web

1. Inicia sesión en la aplicación web
2. Haz clic en el botón **"App Escritorio"** en el navbar
3. El navegador descargará `FAT_Testing.exe`

---

## Uso de la Aplicación de Escritorio

### Instalación

No requiere instalación. Simplemente ejecuta `FAT_Testing.exe`

### Inicio de Sesión

1. Ejecuta `FAT_Testing.exe`
2. Ingresa tu **correo electrónico**
3. Ingresa tu **contraseña**
4. Haz clic en **"Iniciar Sesión"** o presiona Enter

### Pantalla de Bienvenida

Después de iniciar sesión exitosamente:
- Verás un mensaje: **"Hola, [tu_usuario]!"**
- Tu correo electrónico
- Tu rol (admin/user)
- Botón para cerrar la aplicación

---

## Requisitos para Usuarios Finales

### Lo que SÍ necesitan:

- ✅ Windows 7 o superior
- ✅ Conexión a la red donde está la base de datos MySQL
- ✅ Cuenta registrada en el sistema

### Lo que NO necesitan:

- ❌ Python instalado
- ❌ Dependencias adicionales
- ❌ Configuración compleja

---

## Configuración de Conexión

La aplicación usa la misma configuración que la web:

**Archivo**: `config.py`

```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:1234@localhost/fat_testing_db'
```

### Para Redes Locales

Si la aplicación se usará en otra computadora de la red:

1. Cambia `localhost` por la IP del servidor MySQL:
   ```python
   SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:1234@192.168.1.100/fat_testing_db'
   ```

2. Asegúrate de que MySQL permita conexiones remotas:
   ```sql
   GRANT ALL PRIVILEGES ON fat_testing_db.* TO 'root'@'%' IDENTIFIED BY '1234';
   FLUSH PRIVILEGES;
   ```

3. Recompila el ejecutable con la nueva configuración

---

## Estructura de Archivos

```
FAT-Testing-ProyectoTitulo/
│
├── desktop_app.py              # Código fuente de la aplicación
├── build_exe.py                # Script de compilación
├── build_exe.bat               # Script automático (Windows)
│
├── downloads/
│   └── FAT_Testing.exe         # Ejecutable para descargar
│
├── dist/                       # Generado por PyInstaller
│   └── FAT_Testing.exe         # Ejecutable compilado
│
└── build/                      # Archivos temporales (puede eliminarse)
```

---

## Estilos y Diseño

### Colores (Matching con Web)

| Elemento | Color |
|----------|-------|
| Header Login | Gradiente #4F46E5 → #7C3AED (Indigo → Purple) |
| Header Success | #10B981 (Green) |
| Botón Principal | Gradiente Indigo → Purple |
| Botón Hover | Tonos más oscuros |
| Fondo | #f0f4f8 (Light gray-blue) |
| Card | #ffffff (White) |
| Texto Principal | #1F2937 (Dark gray) |
| Texto Secundario | #6B7280 (Gray) |

### Tipografía

- **Fuente principal**: Inter
- **Tamaños**:
  - Título: 20pt Bold
  - Subtítulo: 10pt Regular
  - Labels: 10pt Bold
  - Inputs: 11pt Regular
  - Botones: 12pt Bold

---

## Solución de Problemas

### Error: "No se pudo conectar a la base de datos"

**Causa**: La aplicación no puede acceder a MySQL

**Solución**:
1. Verifica que MySQL esté en ejecución
2. Verifica la IP/hostname en `config.py`
3. Verifica credenciales de acceso
4. Verifica firewall/permisos de red

### Error: "Correo o contraseña incorrectos"

**Causa**: Credenciales inválidas

**Solución**:
1. Verifica el correo electrónico (case-sensitive)
2. Verifica la contraseña
3. Prueba iniciar sesión en la web para confirmar credenciales

### El ejecutable no abre / se cierra inmediatamente

**Causa**: Falta alguna dependencia o error en la compilación

**Solución**:
1. Recompila sin `--windowed` para ver errores:
   ```bash
   pyinstaller --onefile desktop_app.py
   ```
2. Ejecuta desde cmd para ver el error:
   ```bash
   dist\desktop_app.exe
   ```

### El ejecutable es muy pesado (>100 MB)

**Causa**: PyInstaller incluye muchas librerías

**Solución**:
1. Ya se excluyen módulos pesados en `build_exe.py`
2. Para optimizar más, usa UPX:
   ```bash
   pyinstaller --onefile --windowed --upx-dir=C:\path\to\upx desktop_app.py
   ```

---

## Desarrollo Futuro

### Funcionalidades Posibles

- [ ] Procesamiento de archivos FAT desde la app de escritorio
- [ ] Sincronización offline/online
- [ ] Notificaciones de escritorio
- [ ] Actualización automática
- [ ] Soporte multi-idioma
- [ ] Tema oscuro/claro

---

## Seguridad

### Consideraciones

- ✅ Contraseñas hasheadas con Bcrypt
- ✅ Conexión segura a base de datos
- ✅ No se almacenan credenciales localmente
- ✅ Validación de inputs

### Recomendaciones

- Usa SSL/TLS para conexión MySQL en producción
- Cambia credenciales por defecto de MySQL
- Implementa límite de intentos de login fallidos
- Considera usar variables de entorno para credenciales

---

## Licencia

Este proyecto es parte del sistema FAT Testing.

---

## Contacto y Soporte

Para problemas o sugerencias, contacta al equipo de desarrollo.

---

**Versión**: 1.0
**Fecha**: 2025
**Autor**: FAT Testing Team
