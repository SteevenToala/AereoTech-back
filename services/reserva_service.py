import psycopg2.extras
from database import Database
from models.reserva_model import ReservaModel


class ReservaService:

    def crear_reserva(self, usuario_id, vuelo_id, cantidad_asientos):
        conexion = Database.obtener_conexion()
        cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            cursor.execute("""
                SELECT reserva_id, codigo_reserva, total, estado
                FROM crear_reserva_segura(%s, %s, %s)
            """, (
                usuario_id,
                vuelo_id,
                cantidad_asientos
            ))

            fila = cursor.fetchone()
            conexion.commit()

            return {
                "id": fila["reserva_id"],
                "codigo_reserva": fila["codigo_reserva"],
                "total": float(fila["total"]),
                "estado": fila["estado"]
            }

        except Exception as e:
            conexion.rollback()
            raise e

        finally:
            cursor.close()
            conexion.close()

    def listar_mis_reservas(self, usuario_id):
        conexion = Database.obtener_conexion()
        cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            cursor.execute("""
                SELECT 
                    r.id,
                    r.codigo_reserva,
                    r.cantidad_asientos,
                    r.total,
                    r.estado,
                    r.fecha_reserva,
                    v.aerolinea,
                    v.origen,
                    v.destino,
                    v.fecha,
                    v.hora_salida,
                    v.hora_llegada,
                    COALESCE(
                        ARRAY_AGG(av.numero_asiento ORDER BY av.numero_asiento)
                        FILTER (WHERE av.numero_asiento IS NOT NULL),
                        ARRAY[]::VARCHAR[]
                    ) AS asientos
                FROM reservas r
                INNER JOIN vuelos v ON v.id = r.vuelo_id
                LEFT JOIN asientos_vuelo av ON av.reserva_id = r.id
                WHERE r.usuario_id = %s
                GROUP BY 
                    r.id,
                    r.codigo_reserva,
                    r.cantidad_asientos,
                    r.total,
                    r.estado,
                    r.fecha_reserva,
                    v.aerolinea,
                    v.origen,
                    v.destino,
                    v.fecha,
                    v.hora_salida,
                    v.hora_llegada
                ORDER BY r.fecha_reserva DESC
            """, (usuario_id,))

            reservas = []

            for fila in cursor.fetchall():
                reservas.append({
                    "id": fila["id"],
                    "codigo_reserva": fila["codigo_reserva"],
                    "cantidad_asientos": fila["cantidad_asientos"],
                    "total": float(fila["total"]),
                    "estado": fila["estado"],
                    "fecha_reserva": str(fila["fecha_reserva"]),
                    "aerolinea": fila["aerolinea"],
                    "origen": fila["origen"],
                    "destino": fila["destino"],
                    "fecha_vuelo": str(fila["fecha"]),
                    "hora_salida": str(fila["hora_salida"]),
                    "hora_llegada": str(fila["hora_llegada"]),
                    "asientos": list(fila["asientos"])
                })

            return reservas

        finally:
            cursor.close()
            conexion.close()

    def cancelar_reserva(self, usuario_id, reserva_id):
        conexion = Database.obtener_conexion()
        cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            cursor.execute("""
                SELECT vuelo_id, cantidad_asientos, estado
                FROM reservas
                WHERE id = %s
                  AND usuario_id = %s
                FOR UPDATE
            """, (
                reserva_id,
                usuario_id
            ))

            reserva = cursor.fetchone()

            if reserva is None:
                conexion.rollback()
                return None

            if reserva["estado"] != "ACTIVA":
                conexion.rollback()
                return "NO_ACTIVA"

            cursor.execute("""
                UPDATE reservas
                SET estado = 'CANCELADA'
                WHERE id = %s
            """, (reserva_id,))

            cursor.execute("""
                UPDATE asientos_vuelo
                SET estado = 'DISPONIBLE',
                    reserva_id = NULL
                WHERE reserva_id = %s
            """, (reserva_id,))

            cursor.execute("""
                UPDATE vuelos
                SET asientos_disponibles = asientos_disponibles + %s,
                    version = version + 1
                WHERE id = %s
            """, (
                reserva["cantidad_asientos"],
                reserva["vuelo_id"]
            ))
            conexion.commit()
            return "CANCELADA"

        except Exception as e:
            conexion.rollback()
            raise e

        finally:
            cursor.close()
            conexion.close()
