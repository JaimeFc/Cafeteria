from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
# IMPORTANTE: Añadir los campos numéricos y el validador NumberRange
from wtforms import IntegerField, DecimalField 
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from conexion.conexion import conexion, cerrar_conexion

# Este validador se utiliza para verificar que un campo no esté duplicado en la base de datos
def valida_id_no_duplicado(table, field):
    def _validador(form, _field):
        conn = conexion()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {field} = %s", (_field.data,))
        if cursor.fetchone()[0] > 0:
            raise ValidationError(f'Esta cédula ya está registrada.')
        cerrar_conexion(conn)
    return _validador

def valida_email_no_duplicado():
    def _validador(form, field):
        conn = conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email = %s", (field.data,))
        if cursor.fetchone()[0] > 0:
            raise ValidationError(f'Este email ya está registrado.')
        cerrar_conexion(conn)
    return _validador

class ProductoForm(FlaskForm):
    # Función para cargar las opciones de categorías desde la BD
    def cargar_categorias(self):
        conn = conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT ID_Categoria, NombreCategoria FROM categorias ORDER BY NombreCategoria")
        choices = [(str(row[0]), row[1]) for row in cursor.fetchall()]
        cerrar_conexion(conn)
        choices.insert(0, ('', '--- Seleccione Categoría ---')) 
        return choices

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.categoria.choices = self.cargar_categorias() 

    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=120)])
    
    # MODIFICACIÓN CLAVE: IntegerField y NumberRange para cantidad
    cantidad = IntegerField('Cantidad', validators=[
        DataRequired('La cantidad es requerida.'),
        NumberRange(min=0, message='La cantidad debe ser un número entero positivo o cero.')
    ])
    
    # MODIFICACIÓN CLAVE: DecimalField y NumberRange para precio
    precio = DecimalField('Precio', validators=[
        DataRequired('El precio es requerido.'),
        NumberRange(min=0.01, message='El precio debe ser un valor positivo.')
    ], places=2) # 'places=2' indica que acepta 2 decimales
    
    categoria = SelectField('Categoría', validators=[DataRequired(message='Debe seleccionar una categoría.')]) 
    submit = SubmitField('Guardar')

class RegistroForm(FlaskForm):
    idusuario = StringField('Cédula', validators=[DataRequired(), Length(max=10), valida_id_no_duplicado('usuarios', 'idusuario')])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=225), valida_email_no_duplicado()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Ingresar')