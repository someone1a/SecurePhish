from flask import Flask, render_template
from flask_mail import Mail, Message
import os
import json

# Configuración de correo
mail_settings = {
    'MAIL_SERVER': '',
    'MAIL_PORT': 587,
    'MAIL_USE_TLS': True,
    'MAIL_USE_SSL': False,
    'MAIL_USERNAME': '',
    'MAIL_PASSWORD': '',
    'MAIL_DEFAULT_SENDER': ''
}

# Inicialización de la extensión Mail
mail = Mail()

def init_mail(app):
    """Inicializa la extensión Flask-Mail con la aplicación Flask"""
    # Configurar la aplicación con los ajustes de correo
    for key, value in mail_settings.items():
        app.config[key] = value
    
    # Inicializar la extensión Mail con la aplicación
    mail.init_app(app)
    
    return mail

def load_mail_config():
    """Carga la configuración de correo desde el archivo de configuración"""
    config_file = 'mail_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            try:
                config = json.load(f)
                for key, value in config.items():
                    if key.upper() in mail_settings:
                        mail_settings[key.upper()] = value
                return True
            except json.JSONDecodeError:
                print("Error al decodificar el archivo de configuración de correo")
                return False
    return False

def save_mail_config(config):
    """Guarda la configuración de correo en un archivo JSON"""
    config_file = 'mail_config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f)
    return True

def send_phishing_email(recipient_email, subject, campaign_name, sender_name=None):
    """Envía un correo electrónico de phishing a un destinatario"""
    try:
        # Crear el mensaje
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            sender=(sender_name, mail_settings['MAIL_DEFAULT_SENDER']) if sender_name else mail_settings['MAIL_DEFAULT_SENDER']
        )
        
        # Generar la URL de la campaña
        campaign_url = f"/campana/{campaign_name}"
        
        # Renderizar la plantilla de correo
        msg.html = render_template('email_templates/phishing_email.html', 
                                  campaign_url=campaign_url,
                                  recipient_email=recipient_email)
        
        # Enviar el correo
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error al enviar correo: {str(e)}")
        return False

def send_campaign_emails(campaign_name, subject, recipients, sender_name=None):
    """Envía correos electrónicos de phishing a múltiples destinatarios"""
    results = []
    for recipient in recipients:
        success = send_phishing_email(recipient, subject, campaign_name, sender_name)
        results.append({
            'email': recipient,
            'success': success
        })
    return results