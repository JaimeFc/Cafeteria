# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Producto(db.Model):
    __tablename__ = 'productos'
    ID_Producto= db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.String(120), unique=True, nullable=False)
    Cantidad = db.Column(db.Integer, nullable=False, default=0)
    precio = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f'<Producto {self.id} {self.nombre}>'

    def to_tuple(self):
        return (self.ID_Producto, self.Nombre, self.Cantidad, self.precio)