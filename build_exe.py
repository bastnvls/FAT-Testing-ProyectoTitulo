"""
Script para compilar la aplicación de escritorio a un ejecutable .exe
Ejecutar: python build_exe.py
"""

import PyInstaller.__main__
import os
import shutil

def build():
    """Compilar aplicación con PyInstaller"""

    print("=" * 60)
    print("COMPILANDO APLICACIÓN DE ESCRITORIO FAT TESTING")
    print("=" * 60)
    print()

    # Configuración de PyInstaller
    pyinstaller_args = [
        'desktop_app.py',                  # Script principal
        '--name=FAT_Testing',              # Nombre del ejecutable
        '--onefile',                       # Un solo archivo exe
        '--windowed',                      # Sin consola (GUI)
        '--clean',                         # Limpiar archivos temporales
        '--noconfirm',                     # No confirmar sobrescritura

        # Incluir dependencias necesarias
        '--hidden-import=PySide6',
        '--hidden-import=flask',
        '--hidden-import=flask_sqlalchemy',
        '--hidden-import=flask_login',
        '--hidden-import=flask_bcrypt',
        '--hidden-import=pymysql',
        '--hidden-import=email_validator',
        '--hidden-import=models',
        '--hidden-import=config',

        # Excluir módulos innecesarios para reducir tamaño
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=pytest',

        # Opciones adicionales
        '--log-level=INFO',
    ]

    print("Iniciando compilación con PyInstaller...")
    print()

    # Ejecutar PyInstaller
    PyInstaller.__main__.run(pyinstaller_args)

    print()
    print("=" * 60)
    print("✓ COMPILACIÓN COMPLETADA")
    print("=" * 60)
    print()
    print("El ejecutable se encuentra en:")
    print("  → dist/FAT_Testing.exe")
    print()
    print("Tamaño aproximado: 30-50 MB")
    print()
    print("IMPORTANTE: Para que el .exe funcione correctamente:")
    print("1. Debe estar en la misma red que la base de datos MySQL")
    print("2. La base de datos debe estar accesible desde el equipo")
    print("3. Verificar configuración en config.py")
    print()
    print("Para distribuir:")
    print("1. Copia dist/FAT_Testing.exe")
    print("2. Los usuarios pueden ejecutarlo directamente")
    print("3. No necesitan Python instalado")
    print()


if __name__ == '__main__':
    build()
