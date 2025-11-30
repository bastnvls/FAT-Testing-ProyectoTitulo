from flask import Blueprint, request, jsonify
from models import User
from utils import suscripcion_vigente 


# Creamos un "grupo" de rutas llamado 'api
api_bp = Blueprint('api', __name__)

@api_bp.route('/validar-acceso', methods=['POST'])
def validar_acceso_desktop():
    """
    Endpoint consumido por el ejecutable de escritorio.
    Verifica credenciales y estado de suscripción.
    """
    # 1. Recibir datos del ejecutable (formato JSON)
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Datos no recibidos", "permitir_acceso": False}), 400

    email = data.get("email")
    password = data.get("password")

    # 2. Buscar usuario en la BD (La misma BD que usa la web)
    user = User.query.filter_by(email=email).first()

    # 3. Validar si existe y la contraseña es correcta
    if user and user.check_password(password):
        
        # 4. Validar estado de la cuenta (Bloqueo administrativo)
        if user.estado_cuenta != "ACTIVA":
            return jsonify({
                "mensaje": "Tu cuenta nop se encuentra activa. Contacta soporte en la web.",
                "permitir_acceso": False,
                "motivo": "CUENTA_BLOQUEADA"
            }), 403

        # 5. Validar SUSCRIPCIÓN (Usando función 'suscripcion_vigente' de utils.py)
        tiene_suscripcion = suscripcion_vigente(user)

        if tiene_suscripcion:
            # CASO ÉXITO: Usuario existe, pass correcta y pagó.
            return jsonify({
                "mensaje": "Acceso autorizado",
                "permitir_acceso": True,
                "usuario": f"{user.nombre} {user.apellido}",
                "estado_suscripcion": "ACTIVA"
            }), 200
        else:
            # CASO SIN PAGO: Usuario existe, pero no ha pagado o venció.
            return jsonify({
                "mensaje": "Suscripción inactiva o vencida. Por favor renueva en la web.",
                "permitir_acceso": False,
                "motivo": "SIN_SUSCRIPCION",
            }), 403

    # CASO ERROR: Usuario no existe o contraseña mal
    return jsonify({
        "mensaje": "Correo o contraseña incorrectos",
        "permitir_acceso": False,
        "motivo": "CREDENCIALES_INVALIDAS"
    }), 401