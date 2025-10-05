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


# Listar productos con búsqueda dinámica
@app.route('/productos')
@login_required
def listar_productos():
    # Obtener el término de búsqueda (q) y el criterio (criterio)
    q = request.args.get('q', '').strip()
    criterio = request.args.get('criterio', 'nombre') # Valor por defecto: 'nombre'
    
    conn = conexion()
    cursor = conn.cursor(dictionary=True)

    # 1. Definir la consulta base (JOIN para traer el nombre de la categoría)
    query = """
    SELECT 
        p.ID_Producto AS id, 
        p.Nombre AS nombre, 
        p.Cantidad AS cantidad, 
        p.precio,
        c.NombreCategoria AS categoria_nombre 
    FROM productos p
    LEFT JOIN categorias c ON p.ID_Categoria = c.ID_Categoria
    """
    
    params = ()
    
    # 2. Construir la cláusula WHERE basada en el criterio seleccionado
    if q:
        q_like = f"%{q}%" # Para búsquedas parciales (LIKE)
        
        if criterio == 'id' and q.isdigit():
            # Búsqueda por ID (debe ser un número)
            query += " WHERE p.ID_Producto = %s"
            params = (q,)
            
        elif criterio == 'categoria':
            # Búsqueda por Nombre de Categoría
            query += " WHERE c.NombreCategoria LIKE %s"
            params = (q_like,)
            
        elif criterio == 'nombre': # Incluye cualquier otro valor no esperado como 'nombre'
            # Búsqueda por Nombre de Producto (la opción por defecto)
            query += " WHERE p.Nombre LIKE %s"
            params = (q_like,)
            
        else:
            # Si el criterio es ID pero el valor no es número, o hay un criterio inválido
            flash('Búsqueda inválida. Asegúrese de usar un número para buscar por ID.', 'warning')
            q = '' # Limpiamos q para que liste todos sin error

    # 3. Ejecutar la consulta
    if q or not params: # Ejecuta siempre, incluso si q está vacío (para listar todo)
        cursor.execute(query, params)
        productos = cursor.fetchall()
    else:
        # En caso de búsqueda inválida que no ejecutó la consulta
        productos = []

    cerrar_conexion(conn)
    
    # MODIFICACIÓN: Pasamos el criterio de búsqueda a la plantilla
    return render_template('products/list.html', 
                           title='Productos', 
                           productos=productos, 
                           q=q,
                           criterio=criterio)


# Crear producto
@app.route('/productos/nuevo', methods=['GET', 'POST'])
@login_required
def crear_producto():
    form = ProductoForm()
    if form.validate_on_submit():
        conn = conexion()
        try:
            cur = conn.cursor()
            
            # Nuevo: obtener el ID de la categoría del formulario
            id_categoria = form.categoria.data

            # Modificado: la consulta INSERT ahora incluye 'ID_Categoria'
            cur.execute(
                "INSERT INTO productos (Nombre, Cantidad, precio, ID_Categoria) VALUES (%s, %s, %s, %s)",
                (form.nombre.data, form.cantidad.data, float(form.precio.data), id_categoria)
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
    
    # 1. MODIFICACIÓN: Incluir ID_Categoria en la consulta SELECT
    cursor.execute("SELECT ID_Producto AS id, Nombre AS nombre, Cantidad AS cantidad, precio, ID_Categoria FROM productos WHERE ID_Producto = %s", (pid,))
    prod = cursor.fetchone()
    
    if not prod:
        cerrar_conexion(conn)
        return "Producto no encontrado", 404

    # 2. MODIFICACIÓN: Inicializar el formulario con los datos, incluyendo la categoría
    # Es crucial pasar ID_Categoria como string (str()) porque los valores de SelectField son strings.
    form = ProductoForm(data={'nombre': prod['nombre'], 
                              'cantidad': prod['cantidad'], 
                              'precio': prod['precio'],
                              'categoria': str(prod['ID_Categoria'])})

    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        cantidad = form.cantidad.data
        precio = form.precio.data
        # Nuevo: obtener el ID de la categoría del formulario
        id_categoria = form.categoria.data 
        
        try:
            # 3. MODIFICACIÓN: Incluir ID_Categoria en la consulta UPDATE
            cursor.execute("UPDATE productos SET Nombre=%s, Cantidad=%s, precio=%s, ID_Categoria=%s WHERE ID_Producto=%s",
                           (nombre, cantidad, precio, id_categoria, pid))
            conn.commit()
            flash('Producto actualizado correctamente.', 'success')
            return redirect(url_for('listar_productos'))
        except Exception as e:
            conn.rollback()
            form.nombre.errors.append('Error al actualizar el producto. Puede que ya exista otro con ese nombre o problema de categoría: ' + str(e))
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
#FIN DEL SEMESTRE