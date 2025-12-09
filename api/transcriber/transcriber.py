from faster_whisper import WhisperModel
import os
import torch
from django.conf import settings
from .normalize import filterAndNormalize
import logging

logger = logging.getLogger(__name__)

# Constants
ALLOWED_EXTENSIONS = [
    '.wav',
    '.mp3',
    '.mp4',
    '.m4a',
]

# Prompt inicial para condicionar al modelo (Context Priming)
INITIAL_PROMPT = (
    "Transcripción de comunicaciones de control de tráfico aéreo (ATC) en español con terminología en inglés. "
    "Alfabeto ICAO: Alfa, Bravo, Charlie, Delta, Echo, Foxtrot, Golf, Hotel, India, Juliett, Kilo, Lima, Mike, "
    "November, Oscar, Papa, Quebec, Romeo, Sierra, Tango, Uniform, Victor, Whiskey, X-ray, Yankee, Zulu. "
    "Indicativos y Escuelas: Cuatro Vientos, Aerotec, European Flyers, Air Europa, Iberia, Vueling, Ryanair, "
    "Enaire, Cessna, Piper, EC- (Eco Charlie). "
    "Terminología: Rodaje, rodando, pista 27, pista 09, viento, nudos, grados, QNH, autorizado, despegue, "
    "aterrizaje, frustrada, punto de espera, notifique, frecuencia, transpondedor, mil."
)

# FIX CRÍTICO: Asegurar que CTranslate2 encuentre las librerías de NVIDIA
# Esto es necesario porque a veces docker no propaga LD_LIBRARY_PATH correctamente a subprocesos
try:
    if torch.cuda.is_available():
        nvidia_base = os.path.dirname(torch.__file__).replace("torch", "nvidia")
        libs = [
            os.path.join(nvidia_base, "cudnn", "lib"),
            os.path.join(nvidia_base, "cublas", "lib")
        ]
        current_ld = os.environ.get("LD_LIBRARY_PATH", "")
        new_ld = ":".join(libs + [current_ld])
        os.environ["LD_LIBRARY_PATH"] = new_ld
        logger.info(f"GPU Support: Forzando LD_LIBRARY_PATH={new_ld}")
except Exception as e_gpu:
    logger.warning(f"No se pudo configurar path NVIDIA automáticamente: {e_gpu}")

class TranscriptionAgent:
    """
    Agente optimizado de transcripción usando Faster-Whisper (CTranslate2).
    Permite configuración dinámica vía variables de entorno.
    """

    def __init__(self, model_name: str = None):
        """
        Inicializa el modelo Faster-Whisper.

        Args:
            model_name (str): Nombre del modelo Whisper a usar.
                              Si es None, lo toma de settings.WHISPER_MODEL_NAME
                              o por defecto 'jlvdoorn/whisper-large-v3-atco2-asr'
        """
        # Cargar configuración desde settings o usar defaults
        self.model_size = model_name or getattr(settings, 'WHISPER_MODEL_NAME', 'jlvdoorn/whisper-large-v3-atco2-asr')
        
        # Lógica robusta para selección de dispositivo
        if torch.cuda.is_available():
            self.device = 'cuda'
            default_compute = 'float16'
        else:
            self.device = 'cpu'
            default_compute = 'int8'
            
        # Permitir override desde settings
        forced_device = getattr(settings, 'WHISPER_DEVICE', None)
        if forced_device:
            self.device = forced_device

        self.compute_type = getattr(settings, 'WHISPER_COMPUTE_TYPE', default_compute)

        logger.info(f'Iniciando TranscriptionAgent...')
        logger.info(f'Model: {self.model_size}')
        logger.info(f'Device: {self.device}')
        logger.info(f'Compute Type: {self.compute_type}')

        try:
            # Intentamos cargar desde el directorio de conversión personalizado
            ct2_model_dir = "/app/.cache/faster_whisper_converted"
            
            if not os.path.exists(os.path.join(ct2_model_dir, "model.bin")):
                logger.info(f"Model not found in {ct2_model_dir}. Starting conversion of {self.model_size}...")
                
                # Importar convertidor
                import ctranslate2
                
                # Convertir el modelo de HF (PyTorch) a CT2
                converter = ctranslate2.converters.TransformersConverter(
                    self.model_size, 
                    copy_files=["tokenizer.json", "preprocessor_config.json", "vocab.json"]
                )
                
                # Realizar la conversión
                converter.convert(
                    output_dir=ct2_model_dir,
                    quantization=self.compute_type if self.compute_type in ["int8", "float16"] else "int8",
                    force=True
                )
                logger.info("Model conversion completed successfully!")

            # Cargar el modelo ya convertido
            self.model = WhisperModel(
                ct2_model_dir, 
                device=self.device, 
                compute_type=self.compute_type
            )
            logger.info('Faster-Whisper model loaded successfully from converting dir.')

        except Exception as e:
            logger.critical(f'Failed to load/convert Faster-Whisper model: {e}')
            # Fallback a descarga normal si falla la conversión (por si el usuario puso un modelo que YA era CT2)
            try:
                logger.warning("Conversion failed/not needed? Trying direct download...")
                self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            except Exception as e2:
                 logger.critical(f'CRITICAL: Final fallback failed: {e2}')
                 raise e2

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
            logger.error(f'Error: Audio path does not exist: {audio_path}')
            return ''
        
        ext = os.path.splitext(audio_path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.error(f'Error: Invalid extension {ext}')
            return ''

        try:
            logger.info(f'Transcribing file: {audio_path}')
            # Transcribir
            # Configuración temporal: Forzar español si no se especifica
            target_lang = language if language else 'es'
            logger.info(f"Transcribing with language: {target_lang} (Beam=15, Float16)")

            segments, info = self.model.transcribe(
                audio_path, 
                beam_size=15, 
                language=target_lang,
                vad_filter=True, # Voice Activity Detection para saltar silencios
                vad_parameters=dict(min_silence_duration_ms=500),
                initial_prompt=INITIAL_PROMPT
            )

            logger.debug(f'Detected language: {info.language} with probability {info.language_probability}')

            # Faster-Whisper devuelve un generador, iteramos para obtener el texto
            full_text = []
            for segment in segments:
                full_text.append(segment.text)
            
            # Unir todo el texto
            transcription = ' '.join(full_text).strip()

            # Normalización opcional (limpieza de artefactos)
            if normalize:
                transcription = filterAndNormalize(transcription)

            logger.info('Transcription completed.')
            return transcription

        except Exception as e:
            logger.error(f'Error during transcription: {e}')
            return ''

    def is_loaded(self):
        """Devuelve True si el modelo ya está en memoria."""
        return hasattr(self, 'model') and self.model is not None


# Instancia global lazy
_transcriber_instance = None

def get_transcriber_instance():
    global _transcriber_instance
    if _transcriber_instance is None:
        _transcriber_instance = TranscriptionAgent()
    return _transcriber_instance

def is_model_loaded():
    """Chequeo rápido para ver si el modelo está en memoria en este proceso."""
    global _transcriber_instance
    if _transcriber_instance and _transcriber_instance.is_loaded():
        return True
    return False

# Compatibilidad con código existente que importa transcriber_instance
class LazyTranscriberProxy:
    def invoke(self, *args, **kwargs):
        return get_transcriber_instance().invoke(*args, **kwargs)

transcriber_instance = LazyTranscriberProxy()
