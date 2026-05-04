import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import timedelta
import MySQLdb.cursors

app = Flask(__name__)

# ===== CONFIGURACIÓN DE MYSQL =====
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'finex_db'

# ===== SESIÓN =====
app.config['SECRET_KEY'] = 'finex_clave_secreta_cambiar_en_produccion'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# ===== INICIALIZAR MYSQL =====
mysql = MySQL()
mysql.init_app(app)

# ===== TEST DB =====
@app.route('/test-db')
def test_db():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        return "OK DB"
    except Exception as e:
        return f"ERROR: {e}"

# ===== DECORADOR =====
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ===== RUTAS =====
@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/api/registro', methods=['POST'])
def registro():
    try:
        data = request.get_json()

        if not data.get('nombre') or not data.get('email') or not data.get('contraseña'):
            return jsonify({'error': 'Campos requeridos'}), 400

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute('SELECT id FROM usuarios WHERE email = %s', (data['email'],))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Email ya existe'}), 400

        password_hash = generate_password_hash(data['contraseña'])

        cursor.execute('''
            INSERT INTO usuarios (email, contraseña, tipo_cuenta, activo)
            VALUES (%s, %s, %s, %s)
        ''', (data['email'], password_hash, data.get('tipo_cuenta'), True))

        mysql.connection.commit()
        cursor.close()

        return jsonify({'success': True}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute('SELECT * FROM usuarios WHERE email = %s', (data['email'],))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            return jsonify({'error': 'Usuario no existe'}), 401

        if not check_password_hash(user['contraseña'], data['contraseña']):
            return jsonify({'error': 'Contraseña incorrecta'}), 401

        session['usuario_id'] = user['id']
        session['usuario_email'] = user['email']

        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
@login_required
def dashboard():
    return "Bienvenido al dashboard"

if __name__ == '__main__':
    app.run(debug=True)