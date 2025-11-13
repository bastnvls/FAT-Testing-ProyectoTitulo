# Construcción del Ejecutable - FAT Testing

Esta carpeta contiene todos los archivos necesarios para construir el ejecutable (.exe) de la aplicación FAT Testing CLI.

## Archivos

- `build_exe_advanced.py` - Script principal para construir el ejecutable
- `FAT_Testing.spec` - Especificación de PyInstaller para la versión básica
- `FAT_Testing_Pro.spec` - Especificación de PyInstaller para la versión profesional
- `fat_testing_icon.ico` - Icono de la aplicación
- `generate_icon.py` - Script para generar/modificar el icono

## Requisitos

```bash
pip install pyinstaller
```

## Construcción del Ejecutable

### Método 1: Usando el script avanzado

```bash
python build_exe_advanced.py
```

### Método 2: Usando PyInstaller directamente

```bash
# Para versión básica
pyinstaller FAT_Testing.spec

# Para versión profesional
pyinstaller FAT_Testing_Pro.spec
```

## Salida

El ejecutable se generará en la carpeta `dist/` en la raíz del proyecto.

## Notas

- Asegúrate de estar en el directorio raíz del proyecto al ejecutar los comandos
- El ejecutable incluirá todas las dependencias necesarias
- Para distribución, utiliza la carpeta `dist/` completa o el archivo único según la configuración
