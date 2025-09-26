from flask import Flask, render_template, request, redirect, url_for, flash
from conexion.conexion import conexion, cerrar_conexion
from forms import ProductoForm, RegistroForm, LoginForm
from models.models import User
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# Inicialización de Flask y Flask-Login
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Inyectar "now" para usar {{ now().year }} en templates 
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

# Función para recargar el usuario desde la sesión
@login_manager.user_loader
def load_user(user_id):
    return User.obtener_por_idusuario(user_id)

@app.route('/')
def index():
    return render_template('index.html', title='Inicio')

@app.route('/about/')
def about():
    return render_template('about.html', title='Acerca de')

@app.route('/contacto/')
def contacto():
    return render_template('contacto.html', title='Contacto')

# Registro de usuarios
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    form = RegistroForm()
    if form.validate_on_submit():
        idusuario = form.idusuario.data
        nombre = form.nombre.data
        email = form.email.data
        password = form.password.data

        # Generar hash seguro de la contraseña
        password_hash = generate_password_hash(password)

        conn = conexion()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (idusuario, nombre, email, password) VALUES (%s, %s, %s, %s)",
                           (idusuario, nombre, email, password_hash))
            conn.commit()
            flash('Usuario registrado correctamente. Por favor, inicia sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            flash(f'Error al registrar el usuario: {e}', 'danger')
        finally:
            cerrar_conexion(conn)
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {field}: {error}', 'danger')

    return render_template('registro.html', form=form, title='Registro')

# Inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.obtener_por_email(form.email.data)
        print("Email ingresado:", form.email.data)
        print("Contraseña ingresada:", form.password.data)
        print("Usuario encontrado:", user)
        print("Hash en base de datos:", user.password_hash)
        print("¿Coincide la contraseña?:", user.verificar_password(form.password.data))


        if user and user.verificar_password(form.password.data):
            login_user(user)
            flash('¡Inicio de sesión exitoso!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('listar_productos'))
        else:
            flash('Email o contraseña incorrectos.', 'danger')
    return render_template('login.html', form=form, title='Iniciar Sesión')

    

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('index'))

# Listar productos
@app.route('/productos')
@login_required
def listar_productos():
    q = request.args.get('q', '').strip()
    conn = conexion()
    cur = conn.cursor(dictionary=True)
    if q:
        cur.execute("SELECT ID_Producto AS id, Nombre AS nombre, Cantidad AS cantidad, precio FROM productos WHERE Nombre LIKE %s", (f"%{q}%",))
    else:
        cur.execute("SELECT ID_Producto AS id, Nombre AS nombre, Cantidad AS cantidad, precio FROM productos")
    productos = cur.fetchall()
    cerrar_conexion(conn)
    return render_template('products/list.html', title='Productos', productos=productos, q=q)

# Crear producto
@app.route('/productos/nuevo', methods=['GET', 'POST'])
@login_required
def crear_producto():
    form = ProductoForm()
    if form.validate_on_submit():
        conn = conexion()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO productos (Nombre, Cantidad, precio) VALUES (%s, %s, %s)",
                (form.nombre.data, form.cantidad.data, float(form.precio.data))
            )
            conn.commit()
            flash('Producto agregado correctamente.', 'success')
            return redirect(url_for('listar_productos'))
        except Exception as e:
            conn.rollback()
            form.nombre.errors.append('No se pudo guardar: ' + str(e))
        finally:
            cerrar_conexion(conn)
    return render_template('products/form.html', title='Nuevo producto', form=form, modo='crear')

# Editar producto
@app.route('/productos/<int:pid>/editar', methods=['GET', 'POST'])
@login_required
def editar_producto(pid):
    conn = conexion()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ID_Producto AS id, Nombre AS nombre, Cantidad AS cantidad, precio FROM productos WHERE ID_Producto = %s", (pid,))
    prod = cursor.fetchone()
    if not prod:
        cerrar_conexion(conn)
        return "Producto no encontrado", 404

    form = ProductoForm(data={'nombre': prod['nombre'], 'cantidad': prod['cantidad'], 'precio': prod['precio']})

    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        cantidad = form.cantidad.data
        precio = form.precio.data
        try:
            cursor.execute("UPDATE productos SET Nombre=%s, Cantidad=%s, precio=%s WHERE ID_Producto=%s",
                           (nombre, cantidad, precio, pid))
            conn.commit()
            flash('Producto actualizado correctamente.', 'success')
            return redirect(url_for('listar_productos'))
        except Exception as e:
            conn.rollback()
            form.nombre.errors.append('Error al actualizar el producto. Puede que ya exista otro con ese nombre.')
        finally:
            cerrar_conexion(conn)

    cerrar_conexion(conn)
    return render_template('products/form.html', title='Editar producto', form=form, modo='editar', pid=pid)

# Eliminar producto
@app.route('/productos/<int:pid>/eliminar', methods=['POST'])
@login_required
def eliminar_producto(pid):
    conn = conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE ID_Producto = %s", (pid,))
    if cursor.rowcount > 0:
        conn.commit()
        flash('Producto eliminado correctamente.', 'success')
    else:
        flash('Producto no encontrado.', 'warning')
    cerrar_conexion(conn)
    return redirect(url_for('listar_productos'))

if __name__ == '__main__':
    app.run(debug=True)