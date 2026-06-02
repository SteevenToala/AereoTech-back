import hashlib
import secrets
from datetime import datetime, timedelta


class Seguridad:
    @staticmethod
    def generar_hash(password):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def generar_token():
        return secrets.token_hex(32)

    @staticmethod
    def fecha_expiracion_token():
        return datetime.now() + timedelta(minutes=30)
