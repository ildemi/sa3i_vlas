import re
import unicodedata
from .normalization_rules import get_normalization_rules

def apply_text_corrections(text, mistakes_dict):
    """
    Aplica correcciones directas de palabras basándose en el diccionario COMMON_MISTAKES.
    Cubre errores comunes de fonética (Victoria -> Victor) y asegura capitalización.
    """
    words = text.split()
    new_words = []
    
    for word in words:
        clean_word = removeNonAlphaNum(word).lower()
        
        # 1. Búsqueda directa en errores comunes
        if clean_word in mistakes_dict:
            # Reemplazar por la corrección (mantiene case definido en el dict)
            new_words.append(mistakes_dict[clean_word])
        else:
            # Mantiene la palabra original
            new_words.append(word)
            
    return ' '.join(new_words)

def convert_numbers_to_digits(text, number_mapping):
    """
    Convierte números escritos (uno, dos) a dígitos (1, 2) usando NUMBER_MAPPING.
    Usa regex con bordes de palabra (\b) para evitar reemplazar "uno" dentro de "alguno".
    """
    if not number_mapping:
        return text

    # Ordenamos por longitud inversa para reemplazar "diez y seis" antes que "diez" (si hubiera compuestos)
    sorted_nums = sorted(number_mapping.keys(), key=len, reverse=True)
    
    for num_str in sorted_nums:
        # (?i) indica case-insensitive
        # \b asegura palabra completa
        pattern = re.compile(r'\b' + re.escape(num_str) + r'\b', re.IGNORECASE)
        replacement = number_mapping[num_str]
        text = pattern.sub(replacement, text)
        
    return text

def apply_advanced_patterns(text):
    """
    Aplica reemplazos complejos definidos en PATTERN_REPLACEMENTS.
    TODO: Fetch patterns from DB if needed.
    """
    # for regex_pattern, replacement in PATTERN_REPLACEMENTS:
    #     text = re.sub(regex_pattern, replacement, text, flags=re.IGNORECASE)
    return text

# --- Funciones de Limpieza General ---

def removeNonAlphaNum(text):
    return ''.join(c for c in text if c.isalnum() or c == ' ')

def special_characters_binary_to_asci(text):
    # Elimina tildes y diacríticos (á -> a, ñ -> n)
    # Importante para normalizar antes de buscar en diccionarios
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')

# --- Función Principal (Entrypoint) ---

def filterAndNormalize(text):
    """
    Función principal llamada desde el Transcriber.
    Aplica la tubería de limpieza y normalización.
    """
    if not text: 
        return ""
    
    # Cargar reglas desde DB (Cached or Fresh)
    mistakes, numbers = get_normalization_rules()

    # 1. Limpieza básica
    # Convertir a minúsculas iniciales para análisis, pero el output puede cambiar
    # Eliminar caracteres extraños
    cleaned_s1 = removeNonAlphaNum(text)
    
    # 2. Normalización de Números (uno -> 1)
    # Es útil hacerlo antes de las palabras para limpiar contexto
    cleaned_s2 = convert_numbers_to_digits(cleaned_s1, numbers)
    
    # 3. Correcciones de Diccionario (Victoria -> Victor)
    cleaned_s3 = apply_text_corrections(cleaned_s2, mistakes)
    
    # 4. Patrones Avanzados (si los hubiere)
    final_text = apply_advanced_patterns(cleaned_s3)
    
    return final_text
