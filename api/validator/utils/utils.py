import re, unicodedata, csv
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def normalize_text(text):
    """
    Normalizes the input text by removing diacritical marks (e.g., accents) and extra whitespace.

    Args:
        text (str): The input string to normalize.

    Returns:
        str: The normalized string, with accents removed and leading/trailing whitespace stripped.
    """
    # Normaliza el texto y elimina las tildes
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    ).strip()
  
def getRules(path):
    """
    Parses a file containing rules organized in sections and extracts them into a dictionary.

    Args:
        path (str): Path to the file containing rules. The file should have sections indicated by `##` 
                    and rules formatted as `| number. rule_content |`.

    Returns:
        dict: A dictionary where:
              - Keys are section names (as strings).
              - Values are dictionaries where:
                  - Keys are rule numbers (as integers).
                  - Values are rule content (as strings, normalized to lowercase).
    """
    with open(path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    rules_dict = {}
    current_section = None

    # Expresiones regulares para detectar secciones y reglas
    section_pattern = re.compile(r'^##\s*(.*)')
    rule_pattern = re.compile(r'^\|\s*(\d+)\.\s*(.*?)\|')

    for line in lines:
        # Buscar secciones (precedidas por ##)
        section_match = section_pattern.match(line)
        if section_match:
            current_section = section_match.group(1).strip()
            rules_dict[current_section] = {}
            continue
        
        # Buscar reglas (precedidas por números y separadas por '|')
        rule_match = rule_pattern.match(line)
        if rule_match and current_section:
            rule_number = int(rule_match.group(1))
            #rule_content = line.strip()[1:-1].strip()  # Quitar bordes de '|' y espacios
            rules_dict[current_section][rule_number] = (line[0:2] + line[5:]).lower()

    return rules_dict

def remove_text_between_brackets(text):
    """
    Removes all content between parentheses `()` and square brackets `[]` from the input text.

    Args:
        text (str): The input string potentially containing text enclosed in parentheses or square brackets.

    Returns:
        str: The modified string with all content between `()` and `[]` removed, including the brackets themselves.
    """
    # Remove text between () and []
    text = re.sub(r'[\[\(].*?[\]\)]', '', text)
    return text


def calculate_top_similarities(text, text_dict, language, top_n=3):
    """
    Calculates the most similar phrases to text from a text dictionary using TF-IDF similarity.

    Args:
        text (str): The input text to compare.
        text_dict (dict): Dictionary of phrases to search for similarities.
        language (str): Language ("spanish", "english", "mixto").
        top_n (int): Number of most similar phrases to return.

    Returns:
        top_texts (list): List of the most similar original phrases (unmodified).
        top_scores (list): List of corresponding similarity scores.
    """

    # Extract and filter phrases based on the specified language
    text_values_cleaned = []  # List for cleaned phrases
    text_values_original = []  # List for original phrases
    for rules in text_dict.values():
        for rule in rules.values():
            # Select the appropriate part of the rule based on the language
            rule_parts = [part.strip() for part in rule.split('|') if part.strip()]
            if language == 'spanish' and len(rule_parts) > 0:
                selected_rule = rule_parts[0]  # First part corresponds to Spanish
            elif language == 'english' and len(rule_parts) > 1:
                selected_rule = rule_parts[1]  # Second part corresponds to English
            else:
                selected_rule = rule  # Use the entire rule for mixed language or if no match is found

            # Remove text between brackets and normalize the rule for the cleaned version
            cleaned_rule = remove_text_between_brackets(selected_rule)
            text_values_cleaned.append(normalize_text(cleaned_rule))  # Add cleaned rule
            text_values_original.append(normalize_text(selected_rule))  # Add original rule
    
    # Create the TF-IDF vectorizer
    vectorizer = TfidfVectorizer()

    # Concatenate text1 with all phrases and compute the TF-IDF matrix for cleaned phrases
    tfidf_matrix_cleaned = vectorizer.fit_transform([normalize_text(text)] + text_values_cleaned)

    # Compute cosine similarity between text1 (cleaned) and each phrase (cleaned)
    similarity_scores_cleaned = (tfidf_matrix_cleaned[0] * tfidf_matrix_cleaned[1:].T).toarray()[0]

    # Get the indices of the texts with the highest similarity scores
    top_indices_cleaned = np.argsort(similarity_scores_cleaned)[-top_n:][::-1]

    # Create a list of the original texts with the highest scores and their similarity scores, filtering out scores <= 0
    top_texts_original = [text_values_original[i] for i in top_indices_cleaned if similarity_scores_cleaned[i] > 0.2]
    top_scores_original = [similarity_scores_cleaned[i] for i in top_indices_cleaned if similarity_scores_cleaned[i] > 0.2]

    return top_texts_original, top_scores_original


def prepareTextToTTS(text, language):
    """
    Converts a text into a format suitable for Text-to-Speech (TTS) by replacing digits with their word equivalents
    and handling decimal numbers appropriately. Also removes unwanted punctuation marks.

    Args:
        text (str): Input text.
        language (str): Language of the text ('es' for Spanish, any other value defaults to English).

    Returns:
        str: Processed text where:
             - Digits are replaced with their word equivalents.
             - Decimal numbers are formatted with "decimal" separating integer and fractional parts.
             - Unwanted punctuation marks (`,`, `.`, `?`, `!`, `;`) are removed.
    """
    # Diccionario para convertir dígitos a palabras
    if language == 'es':
        numbers = {
            '0': 'cero',
            '1': 'uno',
            '2': 'dos',
            '3': 'tres',
            '4': 'cuatro',
            '5': 'cinco',
            '6': 'seis',
            '7': 'siete',
            '8': 'ocho',
            '9': 'nueve'
        }
    else:
        numbers = {
            '0': 'zero',
            '1': 'one',
            '2': 'two',
            '3': 'three',
            '4': 'four',
            '5': 'five',
            '6': 'six',
            '7': 'seven',
            '8': 'eight',
            '9': 'nine'
        }
    
    # Divide el texto en palabras y símbolos preservando la separación
    tokens = re.findall(r'\d+\.\d+|\d+|[^\s\d]+', text)
    
    # Resultado final
    converted_text = []
    
    for token in tokens:
        # Si es un número decimal
        if token.replace('.', '', 1).isdigit():
            if '.' in token:  # Número decimal
                parts = token.split('.')
                integer_part = ' '.join(numbers[d] for d in parts[0])
                decimal_part = ' '.join(numbers[d] for d in parts[1])
                converted_text.append(f"{integer_part} decimal {decimal_part}")
            else:  # Número entero
                converted_text.append(' '.join(numbers[d] for d in token))
        else:
            # Eliminar signos de puntuación no deseados
            if token in {",", "?", "!", ";", "."}:
                continue
            else:
                converted_text.append(token)
    
    return ' '.join(converted_text)


def process_conversations(conversations_file, scores_file):
    """
    Processes two CSV files: one containing conversations and another containing scores, 
    and combines their data into a dictionary structure.

    Args:
        conversations_file (str): Path to the CSV file containing conversation data. 
                                  This file should have the following columns:
                                  - 'Id Conversación': Unique identifier for each conversation.
                                  - 'Emisor': Sender of the message (e.g., ATCO or pilot).
                                  - 'Conversación': The message content.
        scores_file (str): Path to the CSV file containing scores for each conversation.
                           This file should have the following columns:
                           - 'Id Conversación': Unique identifier for each conversation.
                           - 'Puntuacion callsigns': Score for the correctness of call signs.
                           - 'Puntuacion total': Total score for the conversation.
                           - 'Puntuacion atco': Score for the ATCO's communication.
                           - 'Puntuacion piloto': Score for the pilot's communication.
                           - 'Puntuacion fraseologia': Score for the use of standard phraseology.
                           - 'Puntuacion idioma': Score for language mixing.
                           - 'Puntuacion colacion': Score for collation accuracy.

    Returns:
        dict: A dictionary where keys are conversation IDs and values are dictionaries 
              containing the conversation data and scores. The structure is as follows:
              {
                  'conversation_id': {
                      'conversation': [
                          (sender, message),  # A list of tuples (sender, message content)
                          ...
                      ],
                      'scores': {
                          'call_signs': str,       # Score for call signs
                          'puntuacion_total': str, # Total score
                          'puntuacion_atco': str,  # ATCO's score
                          'puntuacion_piloto': str, # Pilot's score
                          'fraseologia': str,      # Phraseology score
                          'mezcla_idiomas': str,   # Language mixing score
                          'colacion': str         # Collation score
                      }
                  },
                  ...
              }
    """
    # Create a list to store all the conversations
    conversations = {}

    # Open the file with the BOM removed using `utf-8-sig` encoding
    with open(conversations_file, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file, delimiter=';')  # Use ';' as delimiter
        
        # Variables to group conversations by Conversation ID
        current_conversation = []
        previous_conversation_id = None
        
        for row in reader:
            # Extract the Conversation ID and relevant information
            conversation_id = row['Id Conversación']
            
            # If the Conversation ID is empty, stop processing further rows
            if not conversation_id:
                break  # Exit the loop if the conversation ID is empty
            
            sender = row['Emisor'].lower()  # Normalize to lowercase
            message = row['Conversación']
            
            # If the conversation changes, we save the previous one
            if conversation_id != previous_conversation_id:
                if previous_conversation_id is not None:  # Don't do this for the first conversation
                    conversations[previous_conversation_id]['conversation'] = current_conversation
                
                # Initialize a new conversation in the dictionary for the new conversation_id
                if conversation_id not in conversations:
                    conversations[conversation_id] = {'conversation': []}
                
                current_conversation = []
                previous_conversation_id = conversation_id
            
            # Add the tuple (sender, message) to the current conversation
            current_conversation.append((sender, message))
        
        # Make sure to add the last processed conversation if it's not empty
        if current_conversation:
            conversations[previous_conversation_id]['conversation'] = current_conversation

    
    with open(scores_file, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file, delimiter=';')  # Use ';' as delimiter
        for row in reader:
            # Extract the Conversation ID and relevant information
            conversation_id = row['Id Conversación']
            
            # Ensure the conversation_id exists in the conversations dictionary before adding scores
            if conversation_id in conversations:
                conversations[conversation_id]['scores'] = {
                    'call_signs': row['Puntuacion callsigns'],
                    'puntuacion_total': row['Puntuacion total'],
                    'puntuacion_atco': row['Puntuacion atco'],
                    'puntuacion_piloto': row['Puntuacion piloto'],
                    'fraseologia': row['Puntuacion fraseologia'],
                    'mezcla_idiomas': row['Puntuacion idioma'],
                    'colacion': row['Puntuacion colacion']
                }

    return conversations

if __name__ == '__main__':
    print(calculate_top_similarities('tránsito rumbo 200 grados, 70 nudos boeing 737 fl 180 estimado en vor mad a las 23:00',
                                      {'1': {1: '| TRÁNSITO [ADICIONAL] RUMBO (dirección) (tipo de aeronave) (nivel) ESTIMADO EN (o SOBRE) (punto significativo) A LAS (hora)|', 2: 'tránsito, 70'}},
                                      'es'))