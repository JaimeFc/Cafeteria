from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
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
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=120)])
    cantidad = StringField('Cantidad', validators=[DataRequired(), Length(max=120)])
    precio = StringField('Precio', validators=[DataRequired(), Length(max=20)])
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