"""
Script de migración de base de datos para agregar la tabla de tokens de recuperación de contraseña.

Este script actualiza la base de datos existente sin perder datos.
Ejecuta: python migrate_db.py
"""

from __init__ import app
from models import db, PasswordResetToken

def migrate():
    """Crear todas las tablas nuevas sin afectar las existentes"""
    with app.app_context():
        # Crear solo las tablas que no existen
        # db.create_all() es seguro - no sobrescribe tablas existentes
        db.create_all()
        print("✓ Migración completada exitosamente")
        print("✓ Tabla 'password_reset_tokens' creada (si no existía)")
        print("✓ Base de datos actualizada")

if __name__ == '__main__':
    print("Iniciando migración de base de datos...")
    print("=" * 50)
    migrate()
    print("=" * 50)
    print("La base de datos está lista para usar")
    print("\nPróximos pasos:")
    print("1. Configura las variables de entorno en un archivo .env")
    print("2. Ejecuta la aplicación con: python __init__.py")
