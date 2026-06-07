from flask import Flask, request, jsonify
from flask_cors import CORS

from services.usuario_service import UsuarioService
from services.auth_service import AuthService
from services.vuelo_service import VueloService
from services.reserva_service import ReservaService
from services.asiento_service import AsientoService
from services.admin_vuelo_service import AdminVueloService

app = Flask(__name__)
CORS(app)

usuario_service = UsuarioService()
auth_service = AuthService()
vuelo_service = VueloService()
reserva_service = ReservaService()
asiento_service = AsientoService()
admin_vuelo_service = AdminVueloService()

def obtener_usuario_desde_token():
    try:
        auth_header = request.headers.get("Authorization")

        print("obtener")

        if not auth_header:
            return None, jsonify({"error": "Token no enviado"}), 401

        if not auth_header.startswith("Bearer "):
            return None, jsonify({"error": "Formato de token inválido"}), 401

        token = auth_header.replace("Bearer ", "")
        usuario = auth_service.validar_token(token)

        if usuario is None:
            return None, jsonify({"error": "Token inválido o expirado"}), 401
        print("sasdasdsad")
        return usuario, None, None
    except Exception as e:
        print("Error al validar token:", repr(e))
        return None, jsonify({"error": "Error al validar token", "detalle": str(e)}), 500   

@app.route("/")
def inicio():
    return jsonify({
        "mensaje": "API AeroTech Reservas funcionando",
        "arquitectura": "Flutter + Flask + Render + Supabase"
    })


@app.route("/api/usuarios/registro", methods=["POST"])
def registro():
    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({"error": "No se recibió JSON válido"}), 400

    campos = ["usuario", "password", "nombre_completo", "correo", "cedula"]

    for campo in campos:
        if not datos.get(campo):
            return jsonify({"error": f"El campo {campo} es obligatorio"}), 400

    try:
        usuario_id = usuario_service.registrar_usuario(datos)
        return jsonify({
            "mensaje": "Usuario registrado correctamente",
            "usuario_id": usuario_id
        }), 201

    except Exception as e:
        return jsonify({
            "error": "No se pudo registrar el usuario",
            "detalle": str(e)
        }), 500


@app.route("/api/auth/login", methods=["POST"])
def login():
    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({"error": "No se recibió JSON válido"}), 400

    usuario = datos.get("usuario")
    password = datos.get("password")

    if not usuario or not password:
        return jsonify({"error": "Usuario y contraseña son obligatorios"}), 400

    try:
        resultado = auth_service.login(usuario, password)

        if resultado is None:
            return jsonify({"error": "Credenciales inválidas"}), 401

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({
            "error": "No se pudo iniciar sesión",
            "detalle": str(e)
        }), 500


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token no enviado o formato inválido"}), 400

    token = auth_header.replace("Bearer ", "")
    try:
        auth_service.logout(token)
        return jsonify({"mensaje": "Sesión cerrada correctamente"}), 200
    except Exception as e:
        return jsonify({
            "error": "No se pudo cerrar la sesión",
            "detalle": str(e)
        }), 500


@app.route("/api/vuelos", methods=["GET"])
def vuelos():
    print("vuelos????????????????????????????????????????????????????????????????????")
    usuario, error, codigo = obtener_usuario_desde_token()
    print(error, codigo)

    if error:
        return error, codigo

    origen = request.args.get("origen")
    destino = request.args.get("destino")
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")

    # Compatibility: if single 'fecha' is sent, use it as both start and end
    fecha = request.args.get("fecha")
    if fecha and not fecha_inicio and not fecha_fin:
        fecha_inicio = fecha
        fecha_fin = fecha

    try:
        vuelos_disponibles = vuelo_service.buscar_vuelos(origen, destino, fecha_inicio, fecha_fin)
        return jsonify(vuelos_disponibles), 200

    except Exception as e:
        return jsonify({
            "error": "No se pudieron obtener los vuelos",
            "detalle": str(e)
        }), 500


@app.route("/api/reservas", methods=["POST"])
def reservar():
    usuario, error, codigo = obtener_usuario_desde_token()

    if error:
        return error, codigo

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({"error": "No se recibió JSON válido"}), 400

    vuelo_id = datos.get("vuelo_id")
    cantidad_asientos = datos.get("cantidad_asientos")

    if not vuelo_id or not cantidad_asientos:
        return jsonify({"error": "vuelo_id y cantidad_asientos son obligatorios"}), 400

    try:
        reserva = reserva_service.crear_reserva(
            usuario["id"],
            int(vuelo_id),
            int(cantidad_asientos)
        )

        return jsonify({
            "mensaje": "Reserva registrada correctamente",
            "reserva": reserva
        }), 201

    except Exception as e:
        return jsonify({
            "error": "No se pudo registrar la reserva",
            "detalle": str(e)
        }), 400


@app.route("/api/reservas/mis-reservas", methods=["GET"])
def mis_reservas():
    usuario, error, codigo = obtener_usuario_desde_token()

    if error:
        return error, codigo

    try:
        reservas = reserva_service.listar_mis_reservas(usuario["id"])
        return jsonify(reservas), 200

    except Exception as e:
        return jsonify({
            "error": "No se pudieron obtener las reservas",
            "detalle": str(e)
        }), 500


@app.route("/api/reservas/<int:reserva_id>/cancelar", methods=["PUT"])
def cancelar(reserva_id):
    usuario, error, codigo = obtener_usuario_desde_token()

    if error:
        return error, codigo

    try:
        resultado = reserva_service.cancelar_reserva(usuario["id"], reserva_id)

        if resultado is None:
            return jsonify({"error": "Reserva no encontrada"}), 404

        if resultado == "NO_ACTIVA":
            return jsonify({"error": "La reserva no se encuentra activa"}), 400

        return jsonify({"mensaje": "Reserva cancelada correctamente"}), 200

    except Exception as e:
        return jsonify({
            "error": "No se pudo cancelar la reserva",
            "detalle": str(e)
        }), 400

@app.route("/api/reservas/<int:reserva_id>/asientos", methods=["PUT"])
def actualizar_reserva_asientos(reserva_id):
    usuario, error, codigo = obtener_usuario_desde_token()

    if error:
        return error, codigo

    datos = request.get_json(silent=True)
    if not datos:
        return jsonify({"error": "No se recibió JSON válido"}), 400

    asientos = datos.get("asientos")
    if not isinstance(asientos, list) or len(asientos) == 0:
        return jsonify({"error": "Debe seleccionar al menos un asiento"}), 400

    try:
        asiento_service.actualizar_reserva_con_asientos(
            usuario["id"],
            reserva_id,
            asientos
        )
        return jsonify({"mensaje": "Reserva actualizada correctamente", "asientos": asientos}), 200

    except Exception as e:
        return jsonify({
            "error": "No se pudo actualizar la reserva",
            "detalle": str(e)
        }), 400

@app.route("/api/vuelos/<int:vuelo_id>/asientos", methods=["GET"])
def listar_asientos_vuelo(vuelo_id):
    usuario, error, codigo = obtener_usuario_desde_token()

    if error:
        return error, codigo

    try:
        asientos = asiento_service.listar_asientos_por_vuelo(vuelo_id)

        return jsonify(asientos), 200

    except Exception as e:
        return jsonify({
            "error": "No se pudieron obtener los asientos del vuelo",
            "detalle": str(e)
        }), 500
    
@app.route("/api/reservas/asientos", methods=["POST"])
def reservar_asientos():
    usuario, error, codigo = obtener_usuario_desde_token()

    if error:
        return error, codigo

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "error": "No se recibió JSON válido"
        }), 400

    vuelo_id = datos.get("vuelo_id")
    asientos = datos.get("asientos")

    if not vuelo_id:
        return jsonify({
            "error": "El campo vuelo_id es obligatorio"
        }), 400

    if not isinstance(asientos, list) or len(asientos) == 0:
        return jsonify({
            "error": "Debe seleccionar al menos un asiento"
        }), 400

    try:
        reserva = asiento_service.crear_reserva_con_asientos(
            usuario["id"],
            int(vuelo_id),
            asientos
        )

        return jsonify({
            "mensaje": "Reserva registrada correctamente",
            "reserva": reserva
        }), 201

    except Exception as e:
        return jsonify({
            "error": "No se pudo registrar la reserva",
            "detalle": str(e)
        }), 400

@app.route("/api/admin/vuelos", methods=["POST"])
def crear_vuelo():
    usuario, error, codigo = obtener_usuario_desde_token()

    if error:
        return error, codigo

    if usuario.get("rol") != "admin":
        return jsonify({"error": "No tiene permisos de administrador"}), 403

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "error": "No se recibió JSON válido"
        }), 400

    campos = [
        "aerolinea",
        "origen",
        "destino",
        "fecha",
        "hora_salida",
        "hora_llegada",
        "precio",
        "cantidad_asientos"
    ]

    for campo in campos:
        if datos.get(campo) is None or datos.get(campo) == "":
            return jsonify({
                "error": f"El campo {campo} es obligatorio"
            }), 400

    try:
        vuelo = admin_vuelo_service.crear_vuelo_con_asientos(datos)

        return jsonify({
            "mensaje": "Vuelo creado correctamente",
            "vuelo": vuelo
        }), 201

    except Exception as e:
        return jsonify({
            "error": "No se pudo crear el vuelo",
            "detalle": str(e)
        }), 400

@app.route("/api/admin/vuelos/<int:vuelo_id>", methods=["PUT"])
def editar_vuelo(vuelo_id):
    usuario, error, codigo = obtener_usuario_desde_token()

    if error:
        return error, codigo

    if usuario.get("rol") != "admin":
        return jsonify({"error": "No tiene permisos de administrador"}), 403

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "error": "No se recibió JSON válido"
        }), 400

    campos = [
        "aerolinea",
        "origen",
        "destino",
        "fecha",
        "hora_salida",
        "hora_llegada",
        "precio"
    ]

    for campo in campos:
        if datos.get(campo) is None or datos.get(campo) == "":
            return jsonify({
                "error": f"El campo {campo} es obligatorio"
            }), 400

    try:
        vuelo = admin_vuelo_service.editar_vuelo(vuelo_id, datos)

        return jsonify({
            "mensaje": "Vuelo actualizado correctamente",
            "vuelo": vuelo
        }), 200

    except Exception as e:
        return jsonify({
            "error": "No se pudo actualizar el vuelo",
            "detalle": str(e)
        }), 400

@app.route("/api/admin/vuelos/<int:vuelo_id>", methods=["DELETE"])
def eliminar_vuelo(vuelo_id):
    usuario, error, codigo = obtener_usuario_desde_token()

    if error:
        return error, codigo

    if usuario.get("rol") != "admin":
        return jsonify({"error": "No tiene permisos de administrador"}), 403

    try:
        admin_vuelo_service.eliminar_vuelo(vuelo_id)
        return jsonify({"mensaje": "Vuelo eliminado correctamente"}), 200

    except Exception as e:
        return jsonify({
            "error": "No se pudo eliminar el vuelo",
            "detalle": str(e)
        }), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
