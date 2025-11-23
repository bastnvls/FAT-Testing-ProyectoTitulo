"""
Script para compilar la aplicación FAT Testing avanzada
Incluye icono personalizado y optimizaciones
"""

import PyInstaller.__main__
import os
import shutil
import subprocess


def generate_icon():
    """Generar icono si no existe"""
    if not os.path.exists('fat_testing_icon.ico'):
        print("Generando icono profesional...")
        try:
            subprocess.run(['python', 'generate_icon.py'], check=True)
        except:
            print("⚠️  No se pudo generar el icono automáticamente")
            print("   Ejecuta: python generate_icon.py")
            return False
    return True


def build():
    """Compilar aplicación"""

    print("=" * 70)
    print("FAT TESTING - COMPILACIÓN DE APLICACIÓN AVANZADA")
    print("=" * 70)
    print()

    # Generar icono
    has_icon = generate_icon()

    # Configuración de PyInstaller
    args = [
        'desktop_app_advanced.py',
        '--name=FAT_Testing_Pro',
        '--onefile',
        '--windowed',
        '--clean',
        '--noconfirm',

        # Icono
        '--icon=fat_testing_icon.ico' if has_icon else '',

        # Incluir dependencias
        '--hidden-import=PySide6',
        '--hidden-import=flask',
        '--hidden-import=flask_sqlalchemy',
        '--hidden-import=flask_login',
        '--hidden-import=flask_bcrypt',
        '--hidden-import=pymysql',
        '--hidden-import=serial',
        '--hidden-import=models',
        '--hidden-import=config',
        '--hidden-import=cisco_device_tests',
        '--hidden-import=serial_connector',

        # Agregar archivos de datos si los hay
        # '--add-data=templates;templates',

        # Excluir módulos pesados innecesarios
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=pytest',
        '--exclude-module=tkinter',

        # Optimizaciones
        '--log-level=WARN',
    ]

    # Filtrar argumentos vacíos
    args = [arg for arg in args if arg]

    print("Iniciando compilación con PyInstaller...")
    print()
    print("Configuración:")
    print("  • Archivo: desktop_app_advanced.py")
    print("  • Nombre: FAT_Testing_Pro.exe")
    print("  • Modo: Single file (--onefile)")
    print("  • UI: Windowed (sin consola)")
    print(f"  • Icono: {'✓' if has_icon else '✗'}")
    print()

    try:
        PyInstaller.__main__.run(args)

        print()
        print("=" * 70)
        print("✓ COMPILACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 70)
        print()
        print("📁 El ejecutable se encuentra en:")
        print("   → dist/FAT_Testing_Pro.exe")
        print()
        print("📊 Información:")
        exe_path = "dist/FAT_Testing_Pro.exe"
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"   • Tamaño: {size_mb:.2f} MB")
        print()
        print("=" * 70)
        print("PRÓXIMOS PASOS")
        print("=" * 70)
        print()
        print("1. Prueba el ejecutable:")
        print("   cd dist")
        print("   FAT_Testing_Pro.exe")
        print()
        print("2. Para distribuir vía web:")
        print("   copy dist\\FAT_Testing_Pro.exe downloads\\")
        print()
        print("3. Para firma digital (Azure):")
        print("   • Lee AZURE_CODE_SIGNING.md")
        print("   • Configura Azure Trusted Signing")
        print("   • Firma el ejecutable")
        print()
        print("4. Falsas alarmas de antivirus:")
        print("   • La firma digital las elimina")
        print("   • Mientras tanto, agrega exclusión en Windows Defender")
        print("   • Más info en: AZURE_CODE_SIGNING.md")
        print()

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR EN LA COMPILACIÓN")
        print("=" * 70)
        print()
        print(f"Error: {str(e)}")
        print()
        print("Verifica que:")
        print("  • Python 3.8+ está instalado")
        print("  • Todas las dependencias están instaladas:")
        print("    pip install -r requirements.txt")
        print("  • No hay ningún ejecutable anterior en ejecución")
        print()


if __name__ == '__main__':
    build()
