# tenia errores de dedundancia y mejor que la declaracion de la BD sea en un archivo aparte
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Alumno(db.Model):
    __tablename__ = 'alumnos'
    no_control       = db.Column(db.String(20), primary_key=True)
    nombre           = db.Column(db.String(50), nullable=False)
    apellido_paterno = db.Column(db.String(50), nullable=False)
    apellido_materno = db.Column(db.String(50), nullable=False)
    carrera          = db.Column(db.String(100), nullable=False)
    semestre         = db.Column(db.String(20), nullable=False)
    email            = db.Column(db.String(100), nullable=False)
    face_encoding    = db.Column(db.Text, nullable=True)
    foto_path        = db.Column(db.String(255), nullable=True)

class Entradas(db.Model):
    __tablename__ = 'entradas'
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    no_control   = db.Column(db.String(20), db.ForeignKey('alumnos.no_control'), nullable=False)
    fecha_hora   = db.Column(db.DateTime, nullable=False)
    metodo       = db.Column(db.String(20), nullable=False)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id       = db.Column(db.Integer, primary_key=True)
    usuario  = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)