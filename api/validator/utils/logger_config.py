import logging
import colorlog
import os
import pytz
from datetime import datetime

# Crear un directorio de logs si no existe
LOG_DIR = os.path.join('files', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Crear el logger
logger = colorlog.getLogger('VLAS')

# Establecer el nivel de logging para el logger
logger.setLevel(logging.DEBUG)

# Crear un handler de consola
console_handler = colorlog.StreamHandler()

# Crear un handler de archivo para guardar los logs
file_handler = logging.FileHandler(os.path.join(LOG_DIR, 'logfile.log'))

# Configurar los colores para los diferentes niveles de log
log_colors = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}

# Ajustar la hora a la zona horaria local (Europe/Madrid)
class TimezoneFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # Convertir el timestamp a la hora de Madrid (Europe/Madrid)
        madrid_tz = pytz.timezone('Europe/Madrid')
        log_time = datetime.fromtimestamp(record.created, tz=pytz.utc).astimezone(madrid_tz)
        # Devuelve la hora con el formato correcto
        return log_time.strftime('%Y-%m-%d %H:%M:%S')

# Formato del log con la hora incluida
formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    log_colors=log_colors,
    datefmt='%Y-%m-%d %H:%M:%S'  # Formato de la fecha
)
# Asignar el formatter con los colores al handler de consola
console_handler.setFormatter(formatter)

file_formatter = TimezoneFormatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s', '%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_formatter)

logger.handlers.clear()
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Configurar el nivel de logging para otras bibliotecas
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
