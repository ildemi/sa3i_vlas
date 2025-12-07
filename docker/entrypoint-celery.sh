#!/bin/bash
set -e

echo "=== [Celery Entrypoint] ==="
WHISPER_MODEL="${WHISPER_MODEL:-jlvdoorn/whisper-large-v3-atco2-asr}"

echo "Descargando modelo Whisper si no está en cache..."
python - <<PYCODE
from transformers import WhisperForConditionalGeneration
WhisperForConditionalGeneration.from_pretrained("$WHISPER_MODEL")
print("Whisper model listo.")
PYCODE

echo "Iniciando Celery..."
exec "$@"
