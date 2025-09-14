# clase de conexion directa sin sqlalchemy
import mysql.connector
from mysql.connector import Error

# conexion a la base de datos
def conexion():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='desarrollo_web'
    )
# cerrar coneción
def cerrar_conexion(conn):
    if conn.is_connected():
        conn.close()
        print("conexion cerrada")