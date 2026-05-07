import os
from flask import Flask, render_template, request, url_for, session, redirect, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Cargar variables de entorno (DB_USER, DB_PASSWORD, etc.)
load_dotenv()
# hola

app = Flask(__name__)
# Clave para cifrar las sesiones
app.secret_key = os.getenv('SECRET_KEY', 'clave_super_secreta_lumina')

# Configuración de Base de Datos (XAMPP / MySQL)
usuario_db = os.getenv('DB_USER')
contraseña_db = os.getenv('DB_PASSWORD')
host_db = os.getenv('DB_HOST')
nombre_bd = os.getenv('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{usuario_db}:{contraseña_db}@{host_db}/{nombre_bd}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Alumno(db.Model):
    no_control = db.Column(db.String(20), primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    carrera = db.Column(db.String(50), nullable=False)
    semestre = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

# --- SEGURIDAD (MIDDLEWARE) ---
@app.before_request
def verificar_sesion():
    """
    Obliga al login si no hay sesión activa. 
    Excluye la propia página de login y los archivos estáticos.
    """
    rutas_publicas = ['login', 'static']
    
    if 'usuario' not in session and request.endpoint not in rutas_publicas:
        return redirect(url_for('login'))

# --- RUTAS DE NAVEGACIÓN ---

@app.route('/')
def home():
    """Vista principal (Modo Estudiante)."""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el ingreso de administradores."""
    # Si ya hay sesión, lo mandamos directo al dashboard de admin
    if 'usuario' in session: 
        return redirect(url_for('dashboard_admin'))
    
    if request.method == 'POST':
        input_usuario = request.form.get('usuario')
        input_password = request.form.get('password')
        
        user = Usuario.query.filter_by(nombre=input_usuario, password=input_password).first()
        
        if user:
            session['usuario'] = user.nombre
            # Éxito: Redirige a la página aparte (Dashboard Admin)
            return redirect(url_for('dashboard_admin'))
            
        flash('Credenciales incorrectas', 'danger')
        return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Limpia la sesión y manda al login para re-autenticarse."""
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/dashboard_admin')
def dashboard_admin():
    """Página aparte para administración."""
    return render_template('dashboard_admin.html')

# --- RUTAS DE GESTIÓN DE ALUMNOS ---

@app.route('/registrar_alumno')
def registrar_alumno():
    return render_template('registrar_alumno.html', datos=None)

@app.route('/registrar', methods=['POST'])
def registrar():
    data = request.form
    no_control = data['no_control']
    
    existente = Alumno.query.filter_by(no_control=no_control).first()
    if existente:
        flash('Ese número de control ya está registrado.', 'danger')
        return render_template('registrar_alumno.html', datos=data)

    nuevo = Alumno(
        no_control=no_control,
        nombre=data['nombre'],
        apellidos=data['apellidos'],
        carrera=data['carrera'],
        semestre=data['semestre'],
        email=f"{data['email_prefix']}@iguala.tecnm.mx"
    )
    db.session.add(nuevo)
    db.session.commit()
    
    flash('Alumno registrado correctamente.', 'success')
    return redirect(url_for('registrar_alumno'))

@app.route('/buscar_alumno', methods=['POST'])
def buscar_alumno():
    body = request.get_json()
    no_control = (body.get('no_control') or '').strip()
    nombre_busq = (body.get('nombre') or '').strip().lower()

    alumno = None

    if no_control:
        alumno = Alumno.query.filter_by(no_control=no_control).first()

    if not alumno and nombre_busq:
        todos = Alumno.query.all()
        for a in todos:
            nombre_completo = f"{a.nombre} {a.apellidos}".lower()
            if nombre_busq in nombre_completo or nombre_completo in nombre_busq:
                alumno = a
                break

    if alumno:
        return jsonify({
            'encontrado': True,
            'alumno': {
                'nombre': f"{alumno.nombre} {alumno.apellidos}",
                'control': alumno.no_control,
                'carrera': alumno.carrera,
                'semestre': alumno.semestre,
            }
        })
    else:
        return jsonify({'encontrado': False})

if __name__ == '__main__':
    app.run(debug=True)