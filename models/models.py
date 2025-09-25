from flask_login import UserMixin
from conexion.conexion import conexion, cerrar_conexion
from werkzeug.security import check_password_hash

class User(UserMixin):
    def __init__(self, idusuario, nombre, email, password_hash):
        self.id = idusuario  # Flask-Login espera que el ID esté en self.id
        self.nombre = nombre
        self.email = email
        self.password_hash = password_hash

    def verificar_password(self, password_plano: str) -> bool:
        return check_password_hash(self.password_hash, password_plano)

    @staticmethod
    def obtener_por_email(email):
        conn = conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT idusuario, nombre, email, password FROM usuarios WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cerrar_conexion(conn)
        if user_data:
            return User(user_data['idusuario'], user_data['nombre'], user_data['email'], user_data['password'])
        return None

    @staticmethod
    def obtener_por_idusuario(idusuario):
        conn = conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT idusuario, nombre, email, password FROM usuarios WHERE idusuario = %s", (idusuario,))
        user_data = cursor.fetchone()
        cerrar_conexion(conn)
        if user_data:
            return User(user_data['idusuario'], user_data['nombre'], user_data['email'], user_data['password'])
        return None
