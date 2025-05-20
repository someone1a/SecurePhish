
# SecurePhish

**SecurePhish** es una herramienta de prueba de phishing controlado diseñada para simular ataques de phishing en entornos controlados. Su propósito es permitir a las organizaciones probar y evaluar la resistencia de sus empleados frente a ataques de phishing de manera segura y sin comprometer datos reales.

Con **SecurePhish**, puedes crear campañas de phishing personalizadas, seleccionar plantillas predefinidas, capturar credenciales y almacenar los registros de cada intento de phishing.

## Características

- **Interfaz web intuitiva**: Fácil de usar y basada en el navegador.
- **Autenticación segura**: Requiere iniciar sesión para acceder al sistema.
- **Creación de campañas**: Permite crear campañas de phishing personalizadas a partir de plantillas o subiendo archivos HTML.
- **Registros detallados**: Almacena los registros de cada campaña, incluyendo las credenciales capturadas.
- **Plantillas precargadas**: Selecciona plantillas de phishing disponibles para simular campañas de manera rápida.
- **Dashboard intuitivo**: Administrar campañas y ver los registros fácilmente.

## Requisitos

- Python 3.7+
- Flask
- Werkzeug
- Bootstrap (para el diseño)

## Instalación

1. Clona el repositorio:

   ```
   bash
   git clone https://github.com/someone1a/SecurePhish.git
   cd SecurePhish
    ````

2. Crea un entorno virtual y activa el entorno:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # En Windows usa venv\Scripts\activate
   ```

3. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Ejecuta la aplicación:

   ```bash
   python app.py
   ```

   Esto iniciará el servidor de Flask en `http://127.0.0.1:5000`.

## Uso

1. **Primer inicio**: Al acceder a la aplicación por primera vez, te pedirá configurar un usuario y una contraseña en el path `/setup`.

2. **Iniciar sesión**: Después de la configuración inicial, puedes iniciar sesión en `/login` con el usuario y la contraseña configurados.

3. **Crear campañas**: Una vez dentro del dashboard (`/dashboard`), puedes crear campañas seleccionando plantillas precargadas o subiendo tu propio archivo HTML.

4. **Ver campañas activas**: Las campañas creadas aparecerán en el dashboard y podrás ver los registros de las credenciales capturadas.

5. **Ver registros**: Los registros de cada campaña estarán disponibles en el path `/logs/{nombre_campaña}`.

## Estructura del proyecto

```
SecurePhish/
├── app.py                    # Código principal de la aplicación
├── requirements.txt           # Dependencias de Python
├── templates/                 # Plantillas HTML
│   ├── login.html             # Página de login
│   ├── setup.html             # Página de configuración inicial
│   ├── index.html             # Dashboard
│   ├── warning.html           # Página de advertencia después de enviar credenciales
│   └── logs.html              # Página de visualización de logs
├── templates/campaign_templates/  # Plantillas precargadas para phishing
├── campaigns/                 # Directorio donde se guardan las campañas creadas
├── logs/                      # Directorio donde se guardan los logs de cada campaña
└── admin_credentials.txt      # Archivo que guarda las credenciales del primer usuario
```

## Contribuciones

Las contribuciones a **SecurePhish** son bienvenidas. Si tienes una sugerencia, corrección o nueva característica que te gustaría agregar, siéntete libre de crear un `pull request` o abrir un `issue`.

## Seguridad y Responsabilidad

**SecurePhish** está diseñada para ser utilizada únicamente en entornos controlados y con fines educativos o de evaluación de seguridad en sistemas que cuenten con el consentimiento explícito de los usuarios involucrados. **El uso de esta herramienta para realizar ataques de phishing sin la autorización expresa de los usuarios afectados o fuera de un entorno de pruebas controlado es ilegal y puede violar leyes locales e internacionales.**

### Descargo de responsabilidad

El autor de este proyecto **no se hace responsable de ningún uso indebido de esta herramienta**. El usuario acepta que el uso de **SecurePhish** es bajo su propio riesgo y que asume toda la responsabilidad por cualquier consecuencia derivada de su uso, incluidas, pero no limitadas a, consecuencias legales, pérdidas económicas o daños a sistemas informáticos.

El usuario se compromete a **no utilizar esta herramienta para fines maliciosos**, como realizar ataques de phishing sin el consentimiento explícito de los usuarios involucrados. **El uso de esta herramienta para realizar pruebas en sistemas de los cuales no se tiene autorización explícita puede estar penado por la ley.**

**En ningún caso** el autor o los colaboradores de este proyecto serán responsables por daños, pérdidas o cualquier otra consecuencia que surja del uso de **SecurePhish**.


## Licencia


Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.
