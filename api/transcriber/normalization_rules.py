"""
Reglas de normalización para textos transcribidos de ATC.
Ahora carga dinámicamente desde la base de datos (PostgreSQL).
"""
from api.models import TranscriptionCorrection
import logging

logger = logging.getLogger(__name__)

# Cache simple en memoria del worker
_CACHED_RULES = None

def get_normalization_rules():
    """
    Recupera las reglas de normalización de la base de datos.
    Retorna dos diccionarios:
    1. mistakes: Diccionario para reemplazo de palabras completas (token exacto).
    2. numbers: Diccionario para reemplazo por Regex (token border).
    """
    global _CACHED_RULES
    if _CACHED_RULES is not None:
        return _CACHED_RULES
    
    mistakes = {}
    numbers = {}
    
    try:
        # Recuperar todas las correcciones
        corrections = TranscriptionCorrection.objects.all()
        count = 0
        for c in corrections:
            key = c.incorrect_text.lower()
            val = c.correct_text
            
            # Clasificación para estrategia de reemplazo
            # 'nato_alphabet' y 'number' usan Regex (más seguro para "uno", "alpha")
            # 'general', 'terminology', 'airline' usan reemplazo directo de token
            if c.category in ['number', 'nato_alphabet']:
                numbers[key] = val
            else:
                mistakes[key] = val
            count += 1
            
        logger.info(f"Loaded {count} normalization rules from DB.")
        _CACHED_RULES = (mistakes, numbers)
        return _CACHED_RULES
        
    except Exception as e:
        # Fallback si la DB no está lista
        logger.warning(f"Warning: Could not load normalization rules from DB: {e}")
        return ({}, {})

# Backward compatibility placeholders (Deprecated)
COMMON_MISTAKES = {}
NUMBER_MAPPING = {}
PATTERN_REPLACEMENTS = []
