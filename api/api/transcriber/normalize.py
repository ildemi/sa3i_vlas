from whisper.normalizers import EnglishTextNormalizer
normalizer = EnglishTextNormalizer()

import re
import os

# Definiciones de mapeos
nato_alphabet_mapping = {
    'alpha': 'A', 'bravo': 'B', 'charlie': 'C', 'delta': 'D', 'echo': 'E',
    'foxtrot': 'F', 'golf': 'G', 'hotel': 'H', 'india': 'I', 'juliett': 'J',
    'kilo': 'K', 'lima': 'L', 'mike': 'M', 'november': 'N', 'oscar': 'O',
    'papa': 'P', 'quebec': 'Q', 'romeo': 'R', 'sierra': 'S', 'tango': 'T',
    'uniform': 'U', 'victor': 'V', 'whiskey': 'W', 'xray': 'X', 'yankee': 'Y', 'zulu': 'Z',
    'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
    'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
    'zero': '0', 'hundred': '00', 'thousand': '000',
    'decimal': '.', 'comma': ',', 'dash': '-',
    'cero': '0', 'uno': '1', 'dos': '2', 'tres': '3', 'cuatro': '4',
    'cinco': '5', 'seis': '6', 'siete': '7', 'ocho': '8', 'nueve': '9', 'diez': '10'
}


nato_similarities = {
    'alfa': 'alpha', 'oskar': 'oscar', 'ekko': 'echo', 'gulf': 'golf', 'lema': 'lima', 'yanki': 'yankee'
}

terminology_mapping = {
    'FL': 'flight level'
}

text_similarities = {
    'ihear': 'aegean',
    'ajean': 'aegean',
    'ajeant': 'aegean',
    'egian': 'aegean',
    'aegian': 'aegean',
    'aeroflat': 'aeroflot',
    'aeroflotto': 'aeroflot',
    'aeroblott': 'aeroflot',
    'aeroflo': 'aeroflot',
    'air algery': 'air algerie',
    'air algary': 'air algerie',
    'air algira': 'air algerie',
    'air algeria': 'air algerie',
    'aireurova': 'aireuropa',
    'airaropa': 'aireuropa',
    'air nostrumo': 'air nostrum',
    'air nostrun': 'air nostrum',
    'air noestrom': 'air nostrum',
    'air portougal': 'air portugal',
    'air bortugal': 'air portugal',
    'iropa': 'air europa',
    'air friends': 'air france',
    'airfranz': 'airfrans',
    'airfranss': 'airfrans',
    'airfans': 'airfrans',
    'alvastar': 'albastar',
    'albastor': 'albastar',
    'alabaster': 'albastar',
    'albaster': 'albastar',
    'alba star': 'albastar',
    'al buster': 'albastar',
    'alphine': 'alpine',
    'alpin': 'alpine',
    'albine': 'alpine',
    'bablock': 'babcock',
    'babkok': 'babcock',
    'bapcock': 'babcock',
    'beelime': 'beeline',
    'beelane': 'beeline',
    'beelyne': 'beeline',
    'v line': 'beeline',
    'belstarr': 'belstar',
    'vstar': 'belstar',
    'belstir': 'belstar',
    'bellstar': 'belstar',
    'binther': 'binter',
    'bentor': 'binter',
    'vinter': 'binter',
    'blueberd': 'bluebird',
    'bluverd': 'bluebird',
    'blewbird': 'bluebird',
    'bluefinne': 'bluefin',
    'bluven': 'bluefin',
    'blewfin': 'bluefin',
    'bluscan': 'bluescan',
    'bluscan': 'bluescan',
    'bruescan': 'bluescan',
    'bruscan': 'bluescan',
    'blueskam': 'bluescan',
    'brathens': 'braathens',
    'braithens': 'braathens',
    'brathans': 'braathens',
    'brazenz': 'braathens',
    'brazenzs': 'braathens',
    'brazens': 'braathens',
    'raffens': 'braathens',
    'rafens': 'braathens',
    'bratens': 'braathens',
    'britan': 'britannia',
    'beitan': 'britannia',
    'britania': 'britannia',
    'britanea': 'britannia',
    'britanna': 'britannia',
    'britis': 'british',
    'speedbord': 'speedbird',
    'sweetbird': 'speedbird',
    'sidbird': 'speedbird',
    'britiss': 'british',
    'calidonia': 'caledonian',
    'caladonian': 'caledonian',
    'caladonya': 'caledonian',
    'canail': 'canair',
    'canar': 'canair',
    'kanair': 'canair',
    'canaire': 'canair',
    'conair': 'canair',
    'kanary': 'canary',
    'canery': 'canary',
    'canairy': 'canary',
    'chanex': 'channex',
    'chamex': 'channex',
    'chanix': 'channex',
    'janix': 'channex',
    'tannes': 'channex',
    'klikair': 'clickair',
    'clicker': 'clickair',
    'clikair': 'clickair',
    'click here': 'clickair',
    'kondor': 'condor',
    'condur': 'condor',
    'konder': 'condor',
    'cignus': 'cygnus',
    'signus': 'cygnus',
    'cygnuss': 'cygnus',
    'syprus': 'cyprus',
    'cypros': 'cyprus',
    'dagober': 'dagobert',
    'dagoberth': 'dagobert',
    'dagobird': 'dagobert',
    'jack obert': 'dagobert',
    'dal': 'dahl',
    'dull': 'dahl',
    'daal': 'dahl',
    'daalh': 'dahl',
    'denish': 'danish',
    'dannish': 'danish',
    'dainish': 'danish',
    'deltha': 'delta',
    'dalta': 'delta',
    'delter': 'delta',
    'dennim': 'denim',
    'danim': 'denim',
    'demin': 'denim',
    'eze': 'easy',
    'ezee': 'easy',
    'eesy': 'easy',
    'he asi': 'easy',
    'edelvise': 'edelweiss',
    'edelweess': 'edelweiss',
    'edelway': 'edelweiss',
    'egiptear': 'egyptair',
    'egyptaire': 'egyptair',
    'egypair': 'egyptair',
    'eurotranzit': 'eurotransit',
    'eurotrancit': 'eurotransit',
    'urotransit': 'eurotransit',
    'air rings': 'eurowings',
    'eurobins': 'eurowings',
    'urowings': 'eurowings',
    'eurowyns': 'eurowings',
    'eurowins': 'eurowings',
    'hevelo': 'evelop',
    'evelep': 'evelop',
    'evelob': 'evelop',
    'envolop': 'evelop',
    'finair': 'finnair',
    'fynair': 'finnair',
    'finare': 'finnair',
    'fynare': 'finnair',
    'fraktion': 'fraction',
    'frakshon': 'fraction',
    'fractione': 'fraction',
    'france solay': 'france soleil',
    'frans soleil': 'france soleil',
    'france sole': 'france soleil',
    'france solaire': 'france soleil',
    'just air': 'justair',
    'jestair': 'gestair',
    'guestair': 'gestair',
    'gestare': 'gestair',
    'grifin': 'griffin',
    'griffen': 'griffin',
    'gryffin': 'griffin',
    'befin': 'griffin',
    'iberia': 'iberia',
    'ibaria': 'iberia',
    'iberiah': 'iberia',
    'iberiaxpress': 'iberiaexpress',
    'iberiaxpres': 'iberiaexpress',
    'icear': 'iceair',
    'izeair': 'iceair',
    'iceer': 'iceair',
    'japanare': 'japanair',
    'japaner': 'japanair',
    'kayelem': 'klm',
    'kelem': 'klm',
    'klem': 'klm',
    'loftansa': 'lufthansa',
    'left ansa': 'lufthansa',
    'linf answer': 'lufthansa',
    'luftansa kargo': 'lufthansa cargo',
    'luftansacargo': 'lufthansa cargo',
    'lusser': 'luxair',
    'luxaire': 'luxair',
    'luxar': 'luxair',
    'lugsair': 'luxair',
    'nor shutle': 'nor shuttle',
    'nor shuttel': 'nor shuttle',
    'norshuttle': 'nor shuttle',
    'privilige': 'privilege',
    'privilegee': 'privilege',
    'privylege': 'privilege',
    'bostman': 'postman',
    'posman': 'postman',
    'quantas': 'qantas',
    'kantas': 'qantas',
    'qualitea': 'quality',
    'qalitee': 'quality',
    'kwalitee': 'quality',
    'royalmarok': 'royalair maroc',
    'royamoroc': 'royalair maroc',
    'rionair': 'ryanair',
    'ryaner': 'ryanair',
    'runair': 'ryanair',
    'shamrok': 'shamrock',
    'shamroc': 'shamrock',
    'shamrook': 'shamrock',
    'singapoor': 'singapore',
    'singapure': 'singapore',
    'singapour': 'singapore',
    'swess': 'swiss',
    'swis': 'swiss',
    'swees': 'swiss',
    'topswess': 'topswiss',
    'topswis': 'topswiss',
    'topswees': 'topswiss',
    'tooijet': 'tuijet',
    'tuyet': 'tuijet',
    'tuiyet': 'tuijet',
    'twijet': 'tuijet',
    'toonair': 'tunair',
    'tunare': 'tunair',
    'tunayr': 'tunair',
    'verjin': 'virgin',
    'virjin': 'virgin',
    'virgen': 'virgin',
    'volotia': 'volotea',
    'volutea': 'volotea',
    'volotee': 'volotea',
    'viewling': 'vueling',
    'vulling': 'vueling',
    'vweeling': 'vueling',
    'ruling': 'vueling',
    'wizzar': 'wizzair',
    'wizair': 'wizzair',
    'wizer': 'wizzair',
    'wizzrair': 'wizzair',
    'wizzra': 'wizzair',
    'wizzraire': 'wizzair',
    'wizzur': 'wizzair',
    'visaer': 'wizzair',
    'sorex': 'zorex',
    'zorrex': 'zorex',
    'zorrix': 'zorex',
    'zorecks': 'zorex',
    'iteria': 'iberia',
    'imeria': 'iberia',
    'ibelia': 'iberia',
    'berry': 'iberia',
    'eberia': 'iberia',
    'beria': 'iberia',
    'ebaria': 'iberia',
    'iberea': 'iberia',
    'aberea': 'iberia',
    'barrier': 'iberia',
    'iber air': 'iberia',
    'ebarrier': 'iberia',
    'e barrier': 'iberia',
    'rayoner': 'ryanair',
    'rainer': 'ryanair',
    'rayonar': 'ryanair',
    'rayan': 'ryanair',
    'rayan air': 'ryanair',
    'ryan air': 'ryanair',
    'cocho': 'ocho',
    'descent': 'descend',
    'passer': 'pass',
    'new ticket': 'nautical',
    'no secret miles': 'nautical miles',
    'no secret mile': 'nautical mile',
    'calum': 'klm',
    'elite km': 'klm',
    'lklm': 'klm',
    'mklm': 'klm',
    'klme': 'klm',
    'kyle m': 'klm',
    'elk': 'k',
    'elme': 'lm',
    'elke': 'k',
    'sky level': 'skytravel',
    'trevel': 'travel',
    'password': 'pass your',
    'left of track': 'lefthand track',
    'linday': 'sydney',
    'lille': 'sydney',
    'twinne': 'sydney',
    'may ten': 'maintain',
    'climbing maintain': 'climb and maintain',
    'turn write': 'turn right',
    'flight heading': 'fly heading',
    'grow around': 'go around',
    'lethal': 'level',
    'can not act': 'contact',
    'light level': 'flight level',
    'dodger': 'roger',
    'ultimate': 'altimeter',
    'a broach': 'approach',
    'the departure': 'departure',
    'clear ants': 'clearance',
    'reader contact': 'radar contact',
    'squat': 'squawk',
    'tacky': 'taxi',
    'missed a broach': 'missed approach',
    'holding patter': 'holding pattern',
    'breaking action': 'braking action',
    'transport her': 'transponder',
    'turn lift': 'turn left',
    'frequent see': 'frequency',
    'i will less': 'ILS',
    'ilss': 'ILS',
    'local eyes are': 'localizer',
    'view are': 'VOR',
    'and DB': 'NDB',
    'not': 'knot',
    'trium': 'trim',
    'bitch': 'pitch',
    'rather': 'rudder',
    'alien run': 'aileron',
    'flops': 'flaps',
    'store': 'stall',
    'wind sheer': 'wind shear',
    'a DF': 'ADF',
    'may day': 'mayday',
    'hold shore': 'hold short',
    'be afar': 'VFR',
    'eye afar': 'IFR',
    'niner': 'nine',
    'tree': 'three',
    'fife': 'five',
    'sicks': 'six',
    'el puerto': 'helipuerto',
    'sraya': 'xray',
    'premiere': 'inmediate',
    'lorre': 'torre',
    'lorra': 'torre',
    'pistal': 'pista'
}


airlines_oaci_codes = {
    'aegean': 'AEE', 'aeroflot': 'AFL', 'airfrans': 'AFR', 'albastar': 'LAV', 'alpine': 'EJU', 'babcock': 'INR', 'binter': 'IBB', 'iberia': 'IBE', 'ryanair': 'RYR'
}

airlines_iata_codes = {
    'BA': 'british airways', 'KL': 'klm', 'LH': 'lufthansa', 'EW': 'eurowings'
}

airlines_icao_codes = {
    'BAW': 'british airways', 'DLH': 'lufthansa', 'KLM': 'klm', 'EWG': 'eurowings'
}

special_words = ['qnh', 'ils']

def aerospaceTransform(text):
    # Primero, convertir el texto a minúsculas para facilitar las comparaciones
    text = text.lower()

    # Reemplazo de frases completas usando text_similarities
    for phrase, correction in text_similarities.items():
        # Usar expresiones regulares para encontrar la frase completa con límites de palabra
        pattern = re.compile(r'\b' + re.escape(phrase.lower()) + r'\b')
        text = pattern.sub(correction.lower(), text)

    # Luego, dividir el texto en palabras para reemplazos individuales
    wrds = text.split()
    for i, word in enumerate(wrds):
        # Reemplazos de la tabla NATO
        if word.lower() in nato_similarities:
            wrds[i] = nato_similarities[word.lower()]
            word = nato_similarities[word.lower()]
        if word.upper() in terminology_mapping:
            wrds[i] = terminology_mapping[word.upper()]
            word = terminology_mapping[word.upper()]
        if word.lower() in text_similarities:
            wrds[i] = text_similarities[word.lower()]
            word = text_similarities[word.lower()]
        if word.upper() in airlines_iata_codes:
            wrds[i] = airlines_iata_codes[word.upper()]
            word = airlines_iata_codes[word.upper()]
        if word.upper() in airlines_icao_codes:
            wrds[i] = airlines_icao_codes[word.upper()]
            word = airlines_icao_codes[word.upper()]
        if word.lower() in nato_alphabet_mapping:
            wrds[i] = nato_alphabet_mapping[word.lower()]
            word = nato_alphabet_mapping[word.lower()]
        if word.lower() in airlines_oaci_codes:
            wrds[i] = airlines_oaci_codes[word.lower()]
            word = airlines_oaci_codes[word.lower()]
    
    return ' '.join(wrds)

def filterAndNormalize(text):   
    text = removeCharSet(text, '[', ']')
    text = removeCharSet(text, '<', '>')
    #text = removeCharSet(text, '(', ')')
    text = removeNonAlphaNum(text)
    text = separateNumbersAndText(text)
    #text = aerospaceTransform(text)
    #text = removeSpokenSeparators(text)
    # text = separateCallSignLetters(text)
    #text = normalizer(text)
    #text = normalizer(text)
    # Ejecutar dos veces porque el normalizer reemplaza 'zero five' por '05' pero también reemplaza '05' por '5' (eliminando ceros a la izquierda).
    text = splitNumbersIntoDigits(text)
    text = splitGreetings(text)
    #text = remove_multiples(text)
    text = text.lower()
    
    text = special_characters_binary_to_asci(text)
    text = normalizer(text)
    text = aerospaceTransform(text)
    #text = textToNato(text)
    text = join_consecutive_numbers(text)
    text = join_nato_letters(text)
    text = delete_spaces_between_decimals(text)
    text = capitalize_special_words(text)
    
    return text

def textToNato(text: str):
    text = text.lower()
    wrds = text.split()

    for i, word in enumerate(wrds):
        key = next((k for k, v in nato_alphabet_mapping.items() if v == word), None)
        if (key != None):
            wrds[i] = key

    return ' '.join(wrds)

def join_consecutive_numbers(text):
    """
    Une secuencias de números separados por espacios en un solo número.
    Ejemplo: "1 4 2" -> "142"
    """
    pattern = re.compile(r'(\b\d+\b(?:\s+\b\d+\b)+)')
    return pattern.sub(lambda m: ''.join(m.group().split()), text)

def join_nato_letters(text):
    """
    Une secuencias de letras mayúsculas del alfabeto NATO separadas por espacios en una sola palabra.
    Ejemplo: "B C A" -> "BCA"
    """
    nato_letters = set(nato_alphabet_mapping.values())
    pattern = re.compile(r'\b(?:[A-Z]\s+)+[A-Z]\b')

    def replacer(match):
        letters = match.group().split()
        if all(letter in nato_letters for letter in letters):
            return ''.join(letters)
        return match.group()

    return pattern.sub(replacer, text)

# Funciones auxiliares (mantén las demás funciones como están)

def removePunctuation(text):
    text = ''.join(
        ' ' if c in '!@#$%^&*~-+=_\|;:,.?' else c
        for c in text
    )
    return text

def separateNumbersAndText(text):
    text = re.split('(\d+)', text)
    text = ' '.join(text)
    return text

def separateCallSignLetters(text):
    wrds = text.split()
    prohibited_words = ['ILS', 'IFR', 'FL']
    for word in wrds:
        if word.isupper() and word not in prohibited_words:
            ltrs = [str(l) for l in word]
            ltrs = ' '.join(str(l) for l in ltrs)
            x = wrds.index(word)
            wrds[x] = ltrs
    
    return ' '.join(wrds)

def splitNumbersIntoDigits(text):
    words = text.split()
    new_words = []
    for word in words:
        if word.isdigit():
            dgts = []
            for d in word:
                try:
                    dgts.append(int(d))
                except ValueError:
                    # Ignorar caracteres que no se pueden convertir a enteros
                    pass
            new_words.extend([str(d) for d in dgts])
        else:
            new_words.append(word)
    return ' '.join(new_words)

def removeSpokenSeparators(text):
    wrds = text.split()
    for word in wrds:
        if word.lower() in ['decimal', 'comma', 'point']:
            x = wrds.index(word)
            wrds[x] = ''
        
    return ' '.join(wrds)

def splitGreetings(text):
    wrds = text.split()
    for word in wrds:
        if word.lower() in ['goodbye']:
            x = wrds.index(word)
            wrds[x] = 'good bye'
            
    return ' '.join(wrds)

def removeCharSet(text, c1, c2): # for removing all text within (and including) a character set (ex.: [TRANSCRIPT] )
    while c1 in text and c2 in text:
        x = text.find(c1)
        y = text.rfind(c2) # Should be the last entry of the closing element ) ] > 
        text = text[0:x] + text[y+1:]
    return text

def removeChar(text, c1): # for removing a single character (ex.: @ )
    while c1 in text:
        x = text.find(c1)
        text = text[0:x] + text[x+1:]
    return text

def removeNonAlphaNum(text): # for removing all non alphanumeric characters (ex.: ! @ # $ % ^ & * ) (AlphanNum.: A-Z, a-z, 0-9)
    for c in text:
        if not c.isalnum() and c != ' ':
            x = text.find(c)
            text = text[0:x] + text[x+1:]
    return text

def remove_multiples(string):
    for word in string.split():

        first = string.find(word)
        last = string.rfind(word)
        
        substring = string[first:last+len(word)]
        num = substring.count(word)
        if num > 5:
            new_substring = ' '.join([word for i in range(5)]).strip()
            string = string.replace(substring, new_substring)
            
    return string

def standard_words(text):    
    text = text.lower()
    
    text = text.replace('lineup', 'line up')
    text = text.replace('centre', 'center')
    text = text.replace('k l m', 'klm')
    text = text.replace('niner', 'nine')
    text = text.replace('x-ray', 'xray')

    return text

def special_characters_binary_to_asci(text):
    """
    Normalize text by replacing special characters with their basic latin equivalents.
    
    Args:
        text (str): The input text to normalize
        
    Returns:
        str: Normalized text with special characters replaced
    """
    # Dictionary of replacements
    replacements = {
        # Spaces
        '\u00a0': ' ',  # non-breaking space
        
        # Letters with dieresis/umlaut
        '\u00fc': 'u',  # ü
        '\u00f6': 'o',  # ö
        '\u00e4': 'a',  # ä
        '\u00dc': 'U',  # Ü
        '\u00d6': 'O',  # Ö
        '\u00c4': 'A',  # Ä
        
        # Letters with caron/háček
        '\u011b': 'e',  # ě
        '\u0161': 's',  # š
        '\u010d': 'c',  # č
        '\u0159': 'r',  # ř
        '\u017e': 'z',  # ž
        '\u010f': 'd',  # ď
        '\u0165': 't',  # ť
        '\u0148': 'n',  # ň
        '\u010c': 'C',  # Č
        '\u0160': 'S',  # Š
        '\u017d': 'Z',  # Ž
        
        # Letters with acute accent
        '\u00e1': 'a',  # á
        '\u00e9': 'e',  # é
        '\u00ed': 'i',  # í
        '\u00f3': 'o',  # ó
        '\u00fa': 'u',  # ú
        '\u00fd': 'y',  # ý
        '\u00c1': 'A',  # Á
        '\u00c9': 'E',  # É
        '\u00cd': 'I',  # Í
        '\u00d3': 'O',  # Ó
        '\u00da': 'U',  # Ú
        '\u00dd': 'Y',  # Ý
        
        # Letters with grave accent
        '\u00e0': 'a',  # à
        '\u00e8': 'e',  # è
        '\u00ec': 'i',  # ì
        '\u00f2': 'o',  # ò
        '\u00f9': 'u',  # ù
        '\u00c0': 'A',  # À
        '\u00c8': 'E',  # È
        '\u00cc': 'I',  # Ì
        '\u00d2': 'O',  # Ò
        '\u00d9': 'U',  # Ù
        
        # Letters with tilde
        '\u00f1': 'n',  # ñ
        '\u00d1': 'N',  # Ñ
        '\u00e3': 'a',  # ã
        '\u00f5': 'o',  # õ
        '\u00c3': 'A',  # Ã
        '\u00d5': 'O',  # Õ
        
        # Letters with circumflex
        '\u00e2': 'a',  # â
        '\u00ea': 'e',  # ê
        '\u00ee': 'i',  # î
        '\u00f4': 'o',  # ô
        '\u00fb': 'u',  # û
        '\u00c2': 'A',  # Â
        '\u00ca': 'E',  # Ê
        '\u00ce': 'I',  # Î
        '\u00d4': 'O',  # Ô
        '\u00db': 'U',  # Û
        
        # Misc special characters
        '\u00df': 'ss',  # ß (German eszett)
        '\u00e6': 'ae',  # æ
        '\u00c6': 'AE',  # Æ
        '\u0153': 'oe',  # œ
        '\u0152': 'OE'   # Œ
    }
    
    # Apply all replacements
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def normalizeOnly(text):
    return normalizer(text)

def delete_spaces_between_decimals(texto):
    """
    Reemplaza patrones de la forma 'num . num' por 'num.num'.

    Args:
        texto (str): La cadena de texto donde se realizará el reemplazo.

    Returns:
        str: El texto con los patrones reemplazados.
    """
    # Definir el patrón de búsqueda:
    # (\d+)   -> Captura uno o más dígitos (parte izquierda del punto)
    # \s*     -> Captura cero o más espacios en blanco
    # \.      -> Captura el punto literal
    # \s*     -> Captura cero o más espacios en blanco
    # (\d+)   -> Captura uno o más dígitos (parte derecha del punto)
    patron = r'(\d+)\s*\.\s*(\d+)'
    
    # Definir el patrón de reemplazo:
    # \1.\2   -> Reemplaza con el primer grupo de dígitos, un punto y el segundo grupo de dígitos
    reemplazo = r'\1.\2'
    
    # Realizar el reemplazo en todo el texto
    texto_reemplazado = re.sub(patron, reemplazo, texto)
    
    return texto_reemplazado

def capitalize_special_words(texto):
    """
    Reemplaza las palabras especificadas en una cadena de texto por su versión en mayúsculas.

    :param texto: Cadena de texto original.
    :return: Cadena de texto modificada.
    """
    # Crear un patrón de expresión regular que coincida exactamente con las palabras especificadas
    patron = r'\b(' + '|'.join(map(re.escape, special_words)) + r')\b'
    
    # Función de reemplazo que convierte la palabra encontrada a mayúsculas
    def reemplazar(match):
        return match.group(0).upper()
    
    # Realizar el reemplazo en el texto, ignorando mayúsculas/minúsculas
    texto_modificado = re.sub(patron, reemplazar, texto, flags=re.IGNORECASE)
    
    return texto_modificado