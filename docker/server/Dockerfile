FROM python:3.11

# Evitar archivos .pyc y buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Variables para Ollama
ARG ollama_model=phi4
ENV OLLAMA_MODEL=$ollama_model

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no root
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app

# Crear carpetas de cache con permisos correctos
RUN mkdir -p /app/.cache/huggingface /app/.cache/pyannote /tmp/numba_cache \
    && chown -R appuser:appuser /app/.cache /tmp/numba_cache

# Copiar requirements.txt e instalar dependencias
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el resto del proyecto
COPY . /app

# Hacer ejecutables los entrypoints
RUN chmod +x /app/docker/entrypoint-django.sh \
    && chmod +x /app/docker/entrypoint-celery.sh

# Crear carpeta de logs y dar permisos
RUN mkdir -p /app/files/logs && chown -R appuser:appuser /app/files

RUN mkdir -p /app/api/media && chown -R appuser:appuser /app/api/media

# Variables de entorno para cache
ENV HF_HOME=/app/.cache/huggingface
ENV NUMBA_CACHE_DIR=/tmp/numba_cache

# Configuración CRÍTICA para que CTranslate2/Faster-Whisper encuentre las librerías NVIDIA
# Buscamos dinámicamente o hardcodeamos las rutas estándar de pip install nvidia-*
ENV LD_LIBRARY_PATH=/usr/local/lib/python3.11/site-packages/nvidia/cudnn/lib:/usr/local/lib/python3.11/site-packages/nvidia/cublas/lib:$LD_LIBRARY_PATH

# Cambiar a usuario no root
USER appuser

# Exponer puerto de Django
EXPOSE 8002
