import psycopg2.extras
from database import Database
from utils.seguridad import Seguridad


class AuthService:

    def login(self, usuario, password):
        conexion = Database.obtener_conexion()
        cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            password_hash = Seguridad.generar_hash(password)

            cursor.execute("""
                SELECT id, usuario, nombre_completo, correo, rol
                FROM usuarios
                WHERE usuario = %s
                  AND password_hash = %s
                  AND estado = TRUE
            """, (usuario, password_hash))

            fila = cursor.fetchone()

            if fila is None:
                return None

            token = Seguridad.generar_token()
            expiracion = Seguridad.fecha_expiracion_token()

            cursor.execute("""
                INSERT INTO tokens
                (usuario_id, token, fecha_expiracion, activo)
                VALUES (%s, %s,  NOW() + INTERVAL '2 hours', TRUE)
            """, (
                fila["id"],
                token
            ))

            conexion.commit()

            return {
                "mensaje": "Login correcto",
                "usuario": {
                    "id": fila["id"],
                    "usuario": fila["usuario"],
                    "nombre_completo": fila["nombre_completo"],
                    "correo": fila["correo"],
                    "rol": fila["rol"]
                },
                "token": token,
                "expiracion": expiracion.isoformat()
            }

        except Exception as e:
            conexion.rollback()
            raise e

        finally:
            cursor.close()
            conexion.close()

    def validar_token(self, token):
        conexion = Database.obtener_conexion()
        cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            cursor.execute("""
                SELECT u.id, u.usuario, u.nombre_completo, u.correo, u.rol
                FROM tokens t
                INNER JOIN usuarios u ON u.id = t.usuario_id
                WHERE t.token = %s
                  AND t.activo = TRUE
                  AND t.fecha_expiracion > NOW()
                  AND u.estado = TRUE
            """, (token,))

            fila = cursor.fetchone()

            if fila is None:
                return None

            return {
                "id": fila["id"],
                "usuario": fila["usuario"],
                "nombre_completo": fila["nombre_completo"],
                "correo": fila["correo"],
                "rol": fila["rol"]
            }

        finally:
            cursor.close()
            conexion.close()

    def logout(self, token):
        conexion = Database.obtener_conexion()
        cursor = conexion.cursor()

        try:
            cursor.execute("""
                UPDATE tokens
                SET activo = FALSE
                WHERE token = %s
            """, (token,))

            conexion.commit()
            return True

        except Exception as e:
            conexion.rollback()
            raise e

        finally:
            cursor.close()
            conexion.close()
