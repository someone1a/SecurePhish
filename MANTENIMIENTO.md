# Mantenimiento del sistema SecurePhish

## Actualización de dependencias

- Las dependencias del sistema están definidas en el archivo `requirements.txt`.
- Para actualizar o instalar dependencias, ejecutar:
  ```bash
  pip install -r requirements.txt
  ```
- Se recomienda revisar periódicamente las versiones de los paquetes y actualizar según las necesidades del proyecto.

## Gestión de logs

- Los archivos de logs se almacenan en la carpeta `logs/`.
- Revisar periódicamente los logs para identificar errores o comportamientos anómalos.
- Para limpiar logs antiguos, eliminar manualmente los archivos dentro de la carpeta `logs/`.

## Estructura de carpetas y archivos principales

- `app.py`: Archivo principal de la aplicación.
- `requirements.txt`: Dependencias del proyecto.
- `logs/`: Carpeta donde se almacenan los logs.
- `static/`: Archivos estáticos (CSS, JS, imágenes).
- `templates/`: Plantillas HTML.
- `campaigns/`: Información y archivos relacionados con campañas.

## Despliegue y respaldo

- Realizar respaldos periódicos de las carpetas `campaigns/`, `logs/` y la base de datos si aplica.
- Para desplegar el sistema en un nuevo entorno:
  1. Clonar el repositorio o copiar los archivos del proyecto.
  2. Instalar dependencias con `pip install -r requirements.txt`.
  3. Configurar variables de entorno y archivos de configuración si es necesario.
  4. Iniciar el servidor (ver siguiente sección).

## Inicio y detención del servidor

- Para iniciar el servidor, ejecutar:
  ```bash
  python app.py
  ```
- Para detener el servidor, presionar `Ctrl+C` en la terminal donde se está ejecutando.

## Ubicación de archivos de configuración y logs

- Los archivos de configuración suelen estar en el propio `app.py` o en archivos adicionales si se implementan.
- Los logs se encuentran en la carpeta `logs/`.

## Buenas prácticas

- Mantener actualizado el archivo `requirements.txt`.
- Documentar cualquier cambio relevante en el sistema.
- Realizar respaldos antes de actualizaciones mayores.
- Revisar los logs después de cada despliegue o actualización.
