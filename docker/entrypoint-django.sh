#!/bin/bash
set -e

# Variables
PYANNOTE_MODEL="pyannote/speaker-diarization-3.1"
OLLAMA_MODEL="${OLLAMA_MODEL:-phi4}"

echo "=== [Django Entrypoint] ==="

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

echo "Aplicando migraciones..."
python manage.py migrate

echo "Creando superusuario si no existe..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username="${DJANGO_SUPERUSER_USERNAME}").exists():
    User.objects.create_superuser("${DJANGO_SUPERUSER_USERNAME}", "${DJANGO_SUPERUSER_EMAIL}", "${DJANGO_SUPERUSER_PASSWORD}")
END

echo "Descargando modelo de diarización si no está en cache..."
python - << END
from pyannote.audio import Pipeline
Pipeline.from_pretrained("${PYANNOTE_MODEL}", use_auth_token="${HF_TOKEN}")
END

echo "Iniciando servidor Django..."
exec "$@"
