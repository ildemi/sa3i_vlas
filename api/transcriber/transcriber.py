from faster_whisper import WhisperModel
import os
import torch
from django.conf import settings
from .normalize import filterAndNormalize

# Constants
ALLOWED_EXTENSIONS = [
    '.wav',
    '.mp3',
    '.mp4',
    '.m4a',
]

class TranscriptionAgent:
    """
    Agente optimizado de transcripción usando Faster-Whisper (CTranslate2).
    Reemplaza la implementación anterior basada en Transformers/LangGraph para mayor velocidad y menor consumo.
    """

    def __init__(self, model_name: str = "jlvdoorn/whisper-large-v3-atco2-asr"):
        """
        Inicializa el modelo Faster-Whisper.
        
        Args:
            model_name (str): Nombre del modelo Whisper a usar.
                             Por defecto usa 'jlvdoorn/whisper-large-v3-atco2-asr' (ATC Especializado).
        """
        self.model_size = model_name
        
        # Determinar dispositivo y tipo de cómputo
        if torch.cuda.is_available():
            self.device = "cuda"
            # INT8 es mucho más rápido y ligero en VRAM, con pérdida mínima de calidad
            self.compute_type = "int8" 
        else:
            self.device = "cpu"
            self.compute_type = "int8" # CPU también se beneficia de int8

        print(f"Loading Faster-Whisper model '{self.model_size}' on {self.device} with {self.compute_type} precision...")
        
        # Cargar el modelo (se descarga automáticamente la primera vez a huggingface cache)
        self.model = WhisperModel(
            self.model_size, 
            device=self.device, 
            compute_type=self.compute_type
        )
        print("Faster-Whisper model loaded successfully.")

    def invoke(self, audio_path: str, normalize: bool = True, language: str = None):
        """
        Transcribe un archivo de audio.

        Args:
            audio_path (str): Ruta absoluta al archivo de audio.
            normalize (bool): Si True, aplica normalización post-transcripción (limpieza de texto).
            language (str, optional): 'es', 'en' o None para auto-detección.

        Returns:
            str: Texto transcrito.
        """
        if not os.path.exists(audio_path):
            print(f"Error: Audio path does not exist: {audio_path}")
            return ""
        
        ext = os.path.splitext(audio_path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            print(f"Error: Invalid extension {ext}")
            return ""

        try:
            # Transcribir
            # beam_size=5 es el estándar para buena calidad.
            segments, info = self.model.transcribe(
                audio_path, 
                beam_size=5, 
                language=language,
                vad_filter=True, # Voice Activity Detection para saltar silencios
                vad_parameters=dict(min_silence_duration_ms=500)
            )

            # Faster-Whisper devuelve un generador, iteramos para obtener el texto
            full_text = []
            for segment in segments:
                full_text.append(segment.text)
            
            # Unir todo el texto
            transcription = " ".join(full_text).strip()

            # Normalización opcional (limpieza de artefactos)
            if normalize:
                transcription = filterAndNormalize(transcription)

            return transcription

        except Exception as e:
            print(f"Error during transcription: {e}")
            return ""

# Instancia global para ser importada por tasks.py
# Nota: La instanciación carga el modelo en memoria RAM/VRAM. 
# En un entorno worker de Celery con 'fork', esto podría duplicar memoria si no se maneja con cuidado,
# pero para esta escala es aceptable.
transcriber_instance = TranscriptionAgent()