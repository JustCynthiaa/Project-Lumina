from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>¡Hola desde Flask!</h1><p>Texto de prueba</p>"

if __name__ == '__main__':
    app.run(debug=True)