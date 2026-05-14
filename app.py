import os
from flask import Flask, render_template, request, url_for, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'clave_super_secreta_lumina')

# --- CONFIGURACIÓN DE BASE DE DATOS ---
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS ---
class Alumno(db.Model):
    __tablename__ = 'alumnos'
    no_control = db.Column(db.String(20), primary_key=True)
    nombre     = db.Column(db.String(50), nullable=False)
    apellidos  = db.Column(db.String(100), nullable=False)
    carrera    = db.Column(db.String(50), nullable=False)
    semestre   = db.Column(db.Integer, nullable=False)
    email      = db.Column(db.String(100), nullable=False)

class Usuario(db.Model):
    __tablename__ = 'usuarios' 
    id       = db.Column(db.Integer, primary_key=True)
    usuario  = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# --- PREVENIR CACHÉ ---
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# --- RUTAS ---

@app.route('/')
def index():
    
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario_ingresado = request.form.get('usuario')
        password_ingresada = request.form.get('password')
        
        admin = Usuario.query.filter_by(usuario=usuario_ingresado).first()
        
        if admin and admin.password == password_ingresada:
            # 1. Guardamos el estado actual para saber si el kiosco ya estaba abierto
            kiosco_ya_abierto = session.get('admin_logged_in')
            
            # 2. SIEMPRE actualizamos los datos de la sesión con el administrador actual
            session['admin_logged_in'] = True
            session['admin_user'] = admin.usuario
            
            # 3. Redirigimos dependiendo de dónde venía
            if kiosco_ya_abierto:
                return redirect(url_for('panel_administrador'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
            return redirect(url_for('login'))
            
    return render_template('login.html')


@app.route('/admin/panel')
def panel_administrador():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    return render_template('panelAdministrador.html')


@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)