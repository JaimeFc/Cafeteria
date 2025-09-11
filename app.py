from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from datetime import datetime
from models import db, Producto
from forms import ProductoForm
from inventory import Inventario
import json

# Declara la instancia de la aplicación Flask y la configuración
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventario.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key'  # ¡Cambia esto en producción!

# Inicializa la base de datos
db.init_app(app)

# Inyectar "now" para usar {{ now().year }} en plantillas si quieres
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

# Inicializa el inventario en memoria al iniciar la aplicación
with app.app_context():
    db.create_all()
    inventario = Inventario.cargar_desde_bd()

# --- Rutas de páginas principales ---
@app.route('/')
def index():
    return render_template('index.html', title='Inicio')

@app.route('/about/')
def about():
    return render_template('about.html', title='Acerca de')

@app.route('/contacto/')
def contacto():
    return render_template('contacto.html', title='Contacto')


# --- Rutas de Productos (Inventario) ---
@app.route('/productos')
def listar_productos():
    """Muestra la lista de productos y permite la búsqueda."""
    q = request.args.get('q', '').strip()
    productos = inventario.buscar_por_nombre(q) if q else inventario.listar_todos()
    return render_template('products/list.html', title='Productos', productos=productos, q=q)

@app.route('/productos/nuevo', methods=['GET', 'POST'])
def crear_producto():
    """Maneja la creación de un nuevo producto."""
    form = ProductoForm()
    if form.validate_on_submit():
        try:
            inventario.agregar(
                nombre=form.nombre.data,
                cantidad=form.cantidad.data,
                precio=form.precio.data
            )
            flash('Producto agregado correctamente.', 'success')
            return redirect(url_for('listar_productos'))
        except ValueError as e:
            form.nombre.errors.append(str(e))
    return render_template('products/form.html', title='Nuevo producto', form=form, modo='crear')

@app.route('/productos/<int:pid>/editar', methods=['GET', 'POST'])
def editar_producto(pid):
    """Maneja la edición de un producto existente."""
    prod = Producto.query.get_or_404(pid)
    form = ProductoForm(obj=prod)
    if form.validate_on_submit():
        try:
            inventario.actualizar(
                id=pid,
                nombre=form.nombre.data,
                cantidad=form.cantidad.data,
                precio=form.precio.data
            )
            flash('Producto actualizado.', 'success')
            return redirect(url_for('listar_productos'))
        except ValueError as e:
            form.nombre.errors.append(str(e))
    return render_template('products/form.html', title='Editar producto', form=form, modo='editar')

@app.route('/productos/<int:pid>/eliminar', methods=['POST'])
def eliminar_producto(pid):
    """Maneja la eliminación de un producto."""
    ok = inventario.eliminar(pid)
    flash('Producto eliminado.' if ok else 'Producto no encontrado.', 'info' if ok else 'warning')
    return redirect(url_for('listar_productos'))

# --- Nuevas rutas para JSON ---
@app.route('/productos/exportar-json')
def exportar_json():
    """Exporta todos los productos del inventario a un archivo JSON."""
    productos = Producto.query.all()
    lista_productos = [
        {'id': p.id, 'nombre': p.nombre, 'cantidad': p.cantidad, 'precio': p.precio}
        for p in productos
    ]
    # Retorna un JSON con los productos
    return jsonify(lista_productos)

@app.route('/productos/ver-json')
def productos_json():
    """Lee y muestra los productos desde un archivo JSON."""
    try:
        with open('productos.json', 'r') as f:
            productos = json.load(f)
        return render_template('products/list.html', title='Productos (JSON)', productos=productos)
    except FileNotFoundError:
        flash('El archivo productos.json no se encontró.', 'danger')
        return redirect(url_for('listar_productos'))

if __name__ == '__main__':
    app.run(debug=True)