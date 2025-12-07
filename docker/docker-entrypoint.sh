#!/bin/bash
set -e  # Detener ejecución si falla algo

# Variables por defecto si no están definidas
WHISPER_MODEL="${WHISPER_MODEL:-jlvdoorn/whisper-large-v3-atco2-asr}"
OLLAMA_MODEL="${OLLAMA_MODEL:-phi4}"

echo "Descargando modelo Whisper si no está en cache..."
python - <<PYCODE
from transformers import WhisperForConditionalGeneration
WhisperForConditionalGeneration.from_pretrained("$WHISPER_MODEL")
print("Whisper model listo.")
PYCODE

echo "Descargando modelo Ollama si no está en cache..."
python - <<PYCODE
from ollama import Client
client = Client()
try:
    client.pull("$OLLAMA_MODEL")
    print("Ollama model listo.")
except Exception as e:
    print(f"Error descargando Ollama model: {e}")
PYCODE

echo "Ejecutando migraciones..."
python api/manage.py migrate --noinput

echo "Creando superusuario si no existe..."
python api/manage.py shell <<PYCODE
from django.contrib.auth import get_user_model
User = get_user_model()
username = "${DJANGO_SUPERUSER_USERNAME}"
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username,
        "${DJANGO_SUPERUSER_EMAIL}",
        "${DJANGO_SUPERUSER_PASSWORD}"
    )
    print(f"Superusuario {username} creado.")
else:
    print(f"Superusuario {username} ya existe.")
PYCODE

echo "Iniciando aplicación: $@"
exec "$@"
