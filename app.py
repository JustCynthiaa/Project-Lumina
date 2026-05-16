import os
import json
import io
from flask import Flask, render_template, request, url_for, session, redirect, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import base64
import numpy as np
from PIL import Image
import cv2
import face_recognition
from sqlalchemy import or_

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
    no_control       = db.Column(db.String(20), primary_key=True)
    nombre           = db.Column(db.String(50), nullable=False)
    apellido_paterno = db.Column(db.String(50), nullable=False, default='Por Definir')
    apellido_materno = db.Column(db.String(50), nullable=False, default='Por Definir')
    carrera          = db.Column(db.String(100), nullable=False, default='Por Definir')
    semestre         = db.Column(db.String(20), nullable=False, default='Por Definir') 
    email            = db.Column(db.String(100), nullable=False, default='Por Definir')
    
    # CAMPOS BIOMÉTRICOS
    face_encoding    = db.Column(db.Text, nullable=True) 
    foto_path        = db.Column(db.String(255), nullable=True)

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
            kiosco_ya_abierto = session.get('admin_logged_in')

            session['admin_logged_in'] = True
            session['admin_user'] = admin.usuario

            if kiosco_ya_abierto:
                
                return redirect(url_for('admin_bp.panel_administrador'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')





# --- RUTAS DE IA ---
@app.route('/procesar_rostro', methods=['POST'])
def procesar_rostro():
    """Escanea el rostro en vivo y busca si coincide con algún alumno registrado."""
    data = request.get_json()
    imagen_b64 = data.get('imagen', '')

    if not imagen_b64:
        return jsonify({'exito': False, 'mensaje': 'No se recibió imagen.'})

    try:
        # 1. Decodificar la imagen Base64 de forma segura
        if "," in imagen_b64:
            _, encoded = imagen_b64.split(",", 1)
        else:
            encoded = imagen_b64
            
        img_data = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(img_data)).convert('RGB')
        img_array = np.ascontiguousarray(np.array(image, dtype=np.uint8))

        # 2. Localizar el rostro y extraer sus 128 números (encoding)
        face_locations = face_recognition.face_locations(img_array, model='hog')
        
        if len(face_locations) == 0:
            return jsonify({'exito': False, 'mensaje': 'No se detecta rostro. Ilumina mejor tu cara.'})
        elif len(face_locations) > 1:
            return jsonify({'exito': False, 'mensaje': 'Hay más de un rostro en la cámara.'})

        # Extraemos el vector matemático del rostro capturado
        captura_encoding = face_recognition.face_encodings(img_array, face_locations)[0]

        # 3. TRAER DE MYSQL SOLO A LOS ALUMNOS QUE YA TIENEN ROSTRO REGISTRADO
        alumnos_registrados = Alumno.query.filter(Alumno.face_encoding.isnot(None)).all()

        # Si nadie se ha registrado en todo el sistema, evidentemente no habrá coincidencia
        if not alumnos_registrados:
            return jsonify({'exito': False, 'reconocido': False, 'mensaje': 'Rostro no registrado.'})

        # 4. COMPARACIÓN MATEMÁTICA EN LA BASE DE DATOS
        # Convertimos los textos JSON de la base de datos de vuelta a arreglos de Numpy
        lista_encodings_bd = [json.loads(al.face_encoding) for al in alumnos_registrados]
        
        # face_recognition compara la lista completa a una velocidad increíble
        # tolerancia = 0.5 (entre más bajo, más estricto es para evitar que se confunda con otra persona)
        coincidencias = face_recognition.compare_faces(lista_encodings_bd, captura_encoding, tolerance=0.5)

        if True in coincidencias:
            # Buscamos cuál de todos fue el que coincidió primero
            indice_match = coincidencias.index(True)
            alumno_reconocido = alumnos_registrados[indice_match]

            # Formateamos los datos para la Ficha del Estudiante en el Frontend
            nombre_completo = f"{alumno_reconocido.nombre} {alumno_reconocido.apellido_paterno} {alumno_reconocido.apellido_materno}"
            
            return jsonify({
                'exito': True,
                'reconocido': True,
                'mensaje': f'¡Bienvenido, {alumno_reconocido.nombre}!',
                'alumno': {
                    'no_control': alumno_reconocido.no_control,
                    'nombre': nombre_completo,
                    'carrera': alumno_reconocido.carrera
                }
            })

        # Si recorrió todos los registros y no hubo ningún MATCH matemático
        return jsonify({'exito': False, 'reconocido': False, 'mensaje': 'Rostro no registrado.'})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'exito': False, 'mensaje': f'Error interno en el servidor: {str(e)}'})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin/registrar_alumno')
def vista_registrar_alumno():
    """Muestra la interfaz HTML para registrar un nuevo estudiante."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    return render_template('registrar_alumno.html')


@app.route('/api/guardar_alumno', methods=['POST'])
def guardar_alumno():
    """Recibe los datos, la foto, extrae biometría y ACTUALIZA al alumno."""
    data = request.get_json()
    
    no_control = data.get('no_control')
    nombre = data.get('nombre')
    ap_paterno = data.get('apellido_paterno')
    ap_materno = data.get('apellido_materno')
    carrera = data.get('carrera')
    semestre = data.get('semestre')
    email = data.get('email')
    imagen_b64 = data.get('imagen', '')

    if not no_control or not imagen_b64:
        return jsonify({'exito': False, 'mensaje': 'Faltan datos para el registro.'})

    # BUSCAMOS AL ALUMNO EXISTENTE
    alumno = Alumno.query.filter_by(no_control=no_control).first()
    
    if not alumno:
        return jsonify({'exito': False, 'mensaje': 'El alumno no existe en la base de datos.'})

    try:
        if "," in imagen_b64:
            _, encoded = imagen_b64.split(",", 1)
        else:
            encoded = imagen_b64
            
        img_data = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(img_data)).convert('RGB')
        img_array = np.ascontiguousarray(np.array(image, dtype=np.uint8))

        face_locations = face_recognition.face_locations(img_array, model='hog')
        
        if len(face_locations) != 1:
            return jsonify({'exito': False, 'mensaje': 'Debe haber exactamente UN rostro en la cámara.'})
            
        encodings = face_recognition.face_encodings(img_array, face_locations)
        face_encoding_json = json.dumps(encodings[0].tolist())

        # Guardar la foto física en la carpeta
        fotos_dir = os.path.join(app.root_path, 'static', 'fotos_alumnos')
        os.makedirs(fotos_dir, exist_ok=True)
        nombre_archivo = f"{no_control}.jpg"
        ruta_fisica = os.path.join(fotos_dir, nombre_archivo)
        image.save(ruta_fisica)
        
        # ACTUALIZAR (UPDATE) los datos en la base de datos
        alumno.nombre = nombre
        alumno.apellido_paterno = ap_paterno
        alumno.apellido_materno = ap_materno
        alumno.carrera = carrera
        alumno.semestre = semestre
        alumno.email = email
        alumno.face_encoding = face_encoding_json
        alumno.foto_path = f"/static/fotos_alumnos/{nombre_archivo}"
        
        # Guardamos los cambios
        db.session.commit()

        return jsonify({'exito': True, 'mensaje': '¡Registro exitoso!'})

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'exito': False, 'mensaje': f'Error interno: {str(e)}'})

@app.route('/api/buscar_alumnos', methods=['GET'])
def buscar_alumnos():
    """Busca estudiantes en tiempo real por número de control o nombre."""
    query_str = request.args.get('query', '').strip()
    
    if not query_str or len(query_str) < 2:
        return jsonify([])
    
    search = f"%{query_str}%"
    resultados = Alumno.query.filter(
        or_(
            Alumno.no_control.ilike(search),
            Alumno.nombre.ilike(search),
            Alumno.apellido_paterno.ilike(search)
        )
    ).limit(8).all()
    
    alumnos_lista = []
    for al in resultados:
        alumnos_lista.append({
            'no_control': al.no_control,
            'nombre': al.nombre,
            'apellido_paterno': al.apellido_paterno,
            'apellido_materno': al.apellido_materno,
            'carrera': al.carrera,
            'semestre': al.semestre,
            'email': al.email
        })
        
    return jsonify(alumnos_lista)

from appadmin import admin_bp
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)


