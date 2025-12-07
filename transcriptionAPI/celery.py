from __future__ import absolute_import, unicode_literals
import os
import multiprocessing
from celery import Celery

# Configura el entorno de Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transcriptionAPI.settings')

# Cambiar el método de inicio del multiprocesamiento a 'spawn' para evitar problemas con CUDA
#multiprocessing.set_start_method('spawn', force=True)

# Inicializamos Celery
app = Celery('transcriptionAPI')

# Usamos RabbitMQ como el broker
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar las tareas de todos los módulos de apps en Django
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
