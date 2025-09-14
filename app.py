from flask import Flask, render_template, request, redirect, url_for, flash
from conexion.conexion import conexion, cerrar_conexion
from forms import ProductoForm
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key' 

# Inyectar "now" para usar {{ now().year }} en templates si quieres
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

@app.route('/')
def index():
    return render_template('index.html', title='Inicio')

@app.route('/about/')
def about():
    return render_template('about.html', title='Acerca de')

@app.route('/contacto/')
def contacto():
    return render_template('contacto.html', title='Contacto')

# En tu archivo app.py
from flask import jsonify

# ... (otras rutas como la de listar_productos, crear_producto, etc.)

# Rutas de productos
# Listar / Buscar
@app.route('/productos')
def listar_productos():
    q = request.args.get('q', '').strip()
    conn = conexion()
    cur = conn.cursor(dictionary=True)
    # Usando alias para que los nombres de las columnas coincidan con el HTML
    if q:
        cur.execute("SELECT ID_Producto AS id, Nombre AS nombre, Cantidad AS cantidad, precio FROM productos WHERE Nombre LIKE %s", (f"%{q}%",))
    else:
        cur.execute("SELECT ID_Producto AS id, Nombre AS nombre, Cantidad AS cantidad, precio FROM productos")
    productos = cur.fetchall()
    cerrar_conexion(conn)
    return render_template('products/list.html', title='Productos', productos=productos, q=q)

# Crear
@app.route('/productos/nuevo', methods=['GET', 'POST'])
def crear_producto():
    form = ProductoForm()
    if form.validate_on_submit():
        conn = conexion()
        try:
            cur = conn.cursor()
            # Consulta para insertar en la tabla 'productos'
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

# editar producto existente
@app.route('/productos/<int:pid>/editar', methods=['GET', 'POST'])
def editar_producto(pid):
    conn = conexion()
    cursor = conn.cursor(dictionary=True)
    # Usando alias para que los nombres de las columnas coincidan con el formulario
    cursor.execute("SELECT ID_Producto AS id, Nombre AS nombre, Cantidad AS cantidad, precio FROM productos WHERE ID_Producto = %s", (pid,))
    prod = cursor.fetchone()
    if not prod:
        cerrar_conexion(conn)
        return "Producto no encontrado", 404
    
    # Se pasan los datos al formulario como un diccionario
    # Se corrige la clave para que coincida con la consulta SQL
    form = ProductoForm(data={'nombre': prod['nombre'], 'cantidad': prod['cantidad'], 'precio': prod['precio']})
    
    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        cantidad = form.cantidad.data
        precio = form.precio.data
        try:
            # Consulta para actualizar la tabla 'productos'
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

# eliminar producto
@app.route('/productos/<int:pid>/eliminar', methods=['POST'])
def eliminar_producto(pid):
    conn = conexion()
    cursor = conn.cursor()
    # Consulta para eliminar en la tabla 'productos'
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