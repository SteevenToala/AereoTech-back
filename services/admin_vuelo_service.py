import psycopg2.extras
from database import Database


class AdminVueloService:

    def crear_vuelo_con_asientos(self, datos):
        conexion = Database.obtener_conexion()
        cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            cantidad_asientos = int(datos["cantidad_asientos"])

            if cantidad_asientos <= 0:
                raise Exception("La cantidad de asientos debe ser mayor a cero")

            cursor.execute("""
                INSERT INTO vuelos (
                    aerolinea,
                    origen,
                    destino,
                    fecha,
                    hora_salida,
                    hora_llegada,
                    precio,
                    asientos_disponibles,
                    estado
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                RETURNING id, aerolinea, origen, destino, fecha, hora_salida, hora_llegada, precio, asientos_disponibles
            """, (
                datos["aerolinea"],
                datos["origen"],
                datos["destino"],
                datos["fecha"],
                datos["hora_salida"],
                datos["hora_llegada"],
                datos["precio"],
                cantidad_asientos
            ))

            vuelo = cursor.fetchone()
            vuelo_id = vuelo["id"]

            asientos = self.generar_asientos(cantidad_asientos)

            for numero_asiento in asientos:
                cursor.execute("""
                    INSERT INTO asientos_vuelo (
                        vuelo_id,
                        numero_asiento,
                        estado
                    )
                    VALUES (%s, %s, 'DISPONIBLE')
                """, (
                    vuelo_id,
                    numero_asiento
                ))

            conexion.commit()

            return {
                "id": vuelo["id"],
                "aerolinea": vuelo["aerolinea"],
                "origen": vuelo["origen"],
                "destino": vuelo["destino"],
                "fecha": str(vuelo["fecha"]),
                "hora_salida": str(vuelo["hora_salida"]),
                "hora_llegada": str(vuelo["hora_llegada"]),
                "precio": float(vuelo["precio"]),
                "asientos_disponibles": vuelo["asientos_disponibles"],
                "asientos_generados": asientos
            }

        except Exception as e:
            conexion.rollback()
            raise e

        finally:
            cursor.close()
            conexion.close()

    def generar_asientos(self, cantidad):
        letras = ["A", "B", "C", "D"]
        asientos = []

        fila = 1

        while len(asientos) < cantidad:
            for letra in letras:
                if len(asientos) < cantidad:
                    asientos.append(f"{fila}{letra}")
            fila += 1

        return asientos

    def editar_vuelo(self, vuelo_id, datos):
        conexion = Database.obtener_conexion()
        cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            cursor.execute("""
                UPDATE vuelos
                SET aerolinea = %s,
                    origen = %s,
                    destino = %s,
                    fecha = %s,
                    hora_salida = %s,
                    hora_llegada = %s,
                    precio = %s,
                    estado = %s
                WHERE id = %s
                RETURNING id, aerolinea, origen, destino, fecha, hora_salida, hora_llegada, precio, asientos_disponibles, estado
            """, (
                datos["aerolinea"],
                datos["origen"],
                datos["destino"],
                datos["fecha"],
                datos["hora_salida"],
                datos["hora_llegada"],
                datos["precio"],
                datos.get("estado", True),
                vuelo_id
            ))

            vuelo = cursor.fetchone()
            if not vuelo:
                raise Exception("Vuelo no encontrado")

            conexion.commit()

            return {
                "id": vuelo["id"],
                "aerolinea": vuelo["aerolinea"],
                "origen": vuelo["origen"],
                "destino": vuelo["destino"],
                "fecha": str(vuelo["fecha"]),
                "hora_salida": str(vuelo["hora_salida"]),
                "hora_llegada": str(vuelo["hora_llegada"]),
                "precio": float(vuelo["precio"]),
                "asientos_disponibles": vuelo["asientos_disponibles"],
                "estado": vuelo["estado"]
            }

        except Exception as e:
            conexion.rollback()
            raise e

        finally:
            cursor.close()
            conexion.close()

    def eliminar_vuelo(self, vuelo_id):
        conexion = Database.obtener_conexion()
        cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Check for active reservations
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM reservas
                WHERE vuelo_id = %s AND estado = 'ACTIVA'
            """, (vuelo_id,))
            res = cursor.fetchone()
            if res and res["total"] > 0:
                raise Exception("No se puede eliminar el vuelo porque tiene reservas activas.")

            cursor.execute("""
                UPDATE vuelos
                SET estado = FALSE
                WHERE id = %s
                RETURNING id
            """, (vuelo_id,))

            vuelo = cursor.fetchone()
            if not vuelo:
                raise Exception("Vuelo no encontrado")

            conexion.commit()
            return True

        except Exception as e:
            conexion.rollback()
            raise e

        finally:
            cursor.close()
            conexion.close()