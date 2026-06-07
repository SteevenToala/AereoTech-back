import psycopg2.extras
from database import Database
from models.asiento_model import AsientoModel


class AsientoService:

    def listar_asientos_por_vuelo(self, vuelo_id):
        conexion = Database.obtener_conexion()
        cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Check if seats are already generated
            cursor.execute("SELECT COUNT(*) as total FROM asientos_vuelo WHERE vuelo_id = %s", (vuelo_id,))
            resultado = cursor.fetchone()

            if resultado["total"] == 0:
                # Fetch flight capacity to auto-generate seats
                cursor.execute("SELECT asientos_disponibles FROM vuelos WHERE id = %s", (vuelo_id,))
                vuelo = cursor.fetchone()
                if vuelo:
                    cantidad = vuelo["asientos_disponibles"]
                    letras = ["A", "B", "C", "D"]
                    asientos = []
                    fila = 1
                    while len(asientos) < cantidad:
                        for letra in letras:
                            if len(asientos) < cantidad:
                                asientos.append(f"{fila}{letra}")
                        fila += 1

                    for numero_asiento in asientos:
                        cursor.execute("""
                            INSERT INTO asientos_vuelo (vuelo_id, numero_asiento, estado)
                            VALUES (%s, %s, 'DISPONIBLE')
                            ON CONFLICT DO NOTHING
                        """, (vuelo_id, numero_asiento))
                    conexion.commit()

            cursor.execute("""
                SELECT 
                    id,
                    vuelo_id,
                    numero_asiento,
                    estado,
                    reserva_id
                FROM asientos_vuelo
                WHERE vuelo_id = %s
                ORDER BY 
                    CAST(regexp_replace(numero_asiento, '[^0-9]', '', 'g') AS INT),
                    regexp_replace(numero_asiento, '[0-9]', '', 'g')
            """, (vuelo_id,))

            asientos = []

            for fila in cursor.fetchall():
                asiento = AsientoModel.from_row(fila)
                asientos.append(asiento.to_dict())

            return asientos

        finally:
            cursor.close()
            conexion.close()

    def crear_reserva_con_asientos(self, usuario_id, vuelo_id, asientos):
        conexion = Database.obtener_conexion()
        cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            cursor.execute("""
                SELECT 
                    reserva_id,
                    codigo_reserva,
                    total,
                    estado
                FROM crear_reserva_asientos_segura(%s, %s, %s)
            """, (
                usuario_id,
                vuelo_id,
                asientos
            ))

            fila = cursor.fetchone()

            conexion.commit()

            return {
                "id": fila["reserva_id"],
                "codigo_reserva": fila["codigo_reserva"],
                "total": float(fila["total"]),
                "estado": fila["estado"],
                "asientos": asientos
            }

        except Exception as e:
            conexion.rollback()
            raise e

        finally:
            cursor.close()
            conexion.close()

    def actualizar_reserva_con_asientos(self, usuario_id, reserva_id, asientos):
        conexion = Database.obtener_conexion()
        cursor = conexion.cursor()

        try:
            cursor.execute("""
                SELECT actualizar_reserva_asientos_segura(%s, %s, %s)
            """, (
                usuario_id,
                reserva_id,
                asientos
            ))
            conexion.commit()
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            cursor.close()
            conexion.close()