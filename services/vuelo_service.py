import psycopg2.extras
from database import Database
from models.vuelo_model import VueloModel


class VueloService:

    def buscar_vuelos(self, origen=None, destino=None, fecha_inicio=None, fecha_fin=None):
        conexion = Database.obtener_conexion()
        cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            cursor.execute("""
                SELECT id, aerolinea, origen, destino, fecha,
                       hora_salida, hora_llegada, precio,
                       asientos_disponibles
                FROM vuelos
                WHERE estado = TRUE
                  AND asientos_disponibles > 0
                  AND (%s IS NULL OR origen ILIKE %s)
                  AND (%s IS NULL OR destino ILIKE %s)
                  AND (%s IS NULL OR fecha >= %s)
                  AND (%s IS NULL OR fecha <= %s)
                ORDER BY fecha, hora_salida
            """, (
                origen, f"%{origen}%" if origen else None,
                destino, f"%{destino}%" if destino else None,
                fecha_inicio, fecha_inicio,
                fecha_fin, fecha_fin
            ))

            vuelos = []

            for fila in cursor.fetchall():
                vuelos.append(VueloModel.from_row(fila).to_dict())

            return vuelos

        finally:
            cursor.close()
            conexion.close()
