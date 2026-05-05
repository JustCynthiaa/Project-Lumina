import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

usuario = os.getenv('DB_USER')
contraseña = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
nombre_bd = os.getenv('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{usuario}:{contraseña}@{host}/{nombre_bd}'
db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)


# Nota importante: cualquier cambio en el modelo de datos (clases) requiere eliminar la base de datos y crearla nuevamente para reflejar los cambios.
# Esto se hace fácilmente eliminando la base de datos desde phpMyAdmin y luego ejecutando el código nuevamente para que se cree una nueva base de datos con las tablas actualizadas.
# python app.py

with app.app_context():
    db.create_all()

    #usuario admin por defecto
    if not Usuario.query.filter_by(nombre='admin').first():
        admin = Usuario(nombre='admin', password='admin123')
        db.session.add(admin)
        db.session.commit()
        print("Usuario admin creado con éxito.")
    else:
        print("Usuario admin ya existe. Continuando...")


@app.route('/')
def home():
    #return "<h1>¡Hola desde Flask!</h1><p>Texto de prueba</p>"
    return render_template('index.html')
# comentario de Earvin como prueba de commit
if __name__ == '__main__':
    app.run(debug=True)