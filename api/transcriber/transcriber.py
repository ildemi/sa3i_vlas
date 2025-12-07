from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from langchain_ollama.llms import OllamaLLM
import operator
from transformers import WhisperForConditionalGeneration, WhisperProcessor
import torch
from librosa import load

from django.conf import settings
from .normalize import filterAndNormalize
import os

# Constants
ALLOWED_LANGUAGES = [
    None,
    'en',  # English
    'es',  # Spanish
]

ALLOWED_EXTENSIONS = [
    '.wav',
    '.mp3',
    '.mp4',
    '.m4a',
]

# System prompts

general_en = 'Air Traffic Control communications'
nato_en = 'alpha,bravo,charlie,delta,echo,foxtrot,golf,hotel,india,juliett,kilo,lima,mike,november,oscar,papa,quebec,romeo,sierra,tango,uniform,victor,whiskey,xray,yankee,zulu'
terminology_en = 'climb,climbing,descend,descending,passing,feet,knots,degrees,direct,maintain,identified,ILS,VFR,IFR,contact,frequency,turn,right,left,heading,altitude,flight,level,cleared,squawk,approach,runway,established,report,affirm,negative,wilco,roger,radio,radar'

general_es = 'Comunicaciones de Control de Tráfico Aéreo'
nato_es = 'alfa,bravo,charlie,delta,eco,foxtrot,golf,hotel,india,julieta,kilo,lima,mike,noviembre,oscar,papa,quebec,romeo,sierra,tango,uniforme,victor,whiskey,xray,yankee,zulu'
terminology_es = 'ascender,ascendiendo,descender,descendiendo,pasando,pies,nudos,grados,directo,mantener,identificado,ILS,VFR,IFR,contacto,frecuencia,girar,derecha,izquierda,rumbo,altitud,nivel,vuelo,autorizado,squawk,aproximación,pista,establecido,reportar,afirmativo,negativo,wilco,roger,radio,radar'

PROMPT_EN = f"{general_en} {nato_en.replace(',', ' ')} {terminology_en.replace(',', ' ')}".strip()
PROMPT_ES = f"{general_es} {nato_es.replace(',', ' ')} {terminology_es.replace(',', ' ')}".strip()

# New prompt for improved callsign transcription
PROMPT_NEW_EN = 'Air Traffic Control communications,alpha,bravo,charlie,delta,echo,foxtrot,golf,hotel,india,juliett,kilo,lima,mike,november,oscar,papa,quebec,romeo,sierra,tango,uniform,victor,whiskey,xray,yankee,zulu,tower,aegan,aeroflot,binter,speedbird,delta,denim,easy,eurowings,evelop,finnair,fraction,gestair,griffin,iberia,klm,lufthansa,quality,ryanair,tui'



SYSTEM_PROMPT_EN = """
# Role

You are an expert in selecting transcripts of conversations between an air traffic controller and a pilot.

# Task

Select the most probable and correct transcription among multiple conversations between an air traffic controller and a pilot, prioritizing those transcriptions that follow the structure callsign + command + value.

# Steps

- Structure Verification: Identify the transcriptions that follow the structure of callsign + command + value. Prioritize these transcriptions over those that do not.
- Analysis of Each Transcription: Evaluate the clarity, coherence, and plausibility of each transcription to determine its accuracy, focusing first on those with the correct structure.
- Comparison of Transcript Details: Examine the correctness of the terminology and procedural language used in air traffic communications.
- Consistency Verification: Ensure that the transcription is consistent with typical aviation communication protocols.
- Callsign Verification: Check the airline name and callsign against the provided list.
- Selection of the Best Transcription: Choose the transcription that demonstrates the highest likelihood of being accurate and representative of an authentic exchange, giving preference to those that follow the structure callsign + command + value.

# Output Format

The output should be the selected transcription verbatim, presented as plain text without any alterations. ONLY THE SELECTED TRANSCRIPTION, NOTHING ELSE.

#Common Vocabulary

{PROMPT_EN}

# Airline Names

- aegean
- aeroflot
- air algerie
- aireuropa
- air nostrum
- air portugal
- airfrans
- albastar
- alpine
- babcock
- bee-line
- belstar
- binter
- bluebird
- bluefin
- bluescan
- braathens
- britannia
- british
- speedbird
- caledonian
- canair
- canary
- channex
- clickair
- condor
- cygnus
- cyprus
- dagobert
- dahl
- danish
- delta
- denim
- easy
- edelweiss
- egyptair
- eurotransit
- eurowings
- evelop
- finnair
- fraction
- france soleil
- gestair
- griffin
- iberia
- iberiaexpress
- iceair
- japanair
- klm
- lufthansa
- lufthansa cargo
- luxair
- nor shuttle
- privilege
- postman
- qantas
- quality
- royalair maroc
- ryanair
- shamrock
- singapore
- swiss
- topswiss
- tuijet
- tunair
- virgin
- volotea
- vueling
- wizzair
- zorex


# Cities

- Sydney
- Tokyo
- New York
- London
- Paris
- Rome
- Berlin
- Madrid
- Barcelona
- Dubai
- Hong Kong
- Los Angeles
- Toronto
- Singapore
- San Francisco
- Mexico City
- Buenos Aires
- Cape Town
- Moscow
- Beijing
- Seoul
- Amsterdam
- Vienna
- Bangkok
- Istanbul
- Rio de Janeiro
- Mumbai
- Cairo
- Melbourne
- Athens

# Transcripts
""".strip()

SYSTEM_PROMPT_ES = """
# Rol

Eres un experto en seleccionar transcripciones de conversaciones entre un controlador aéreo y un piloto.

# Tarea

Selecciona la transcripción más probable y correcta entre múltiples conversaciones entre un controlador aéreo y un piloto, priorizando aquellas transcripciones que sigan la estructura indicativo + comando + valor.

# Pasos

- Verificación de Estructura: Identifica las transcripciones que sigan la estructura de indicativo + comando + valor. Prioriza estas transcripciones sobre las que no la sigan.
- Análisis de Cada Transcripción: Evalúa la claridad, coherencia y plausibilidad de cada transcripción para determinar su precisión, enfocándote primero en aquellas con la estructura correcta.
- Comparación de Detalles de la Transcripción: Examina la precisión de la terminología y el lenguaje procedimental utilizado en las comunicaciones de tráfico aéreo.
- Verificación de Consistencia: Asegúrate de que la transcripción sea consistente con los protocolos típicos de comunicación en aviación.
- Verificación del Indicativo: Comprueba el nombre de la aerolínea y el indicativo en la lista proporcionada.
- Selección de la Mejor Transcripción: Elige la transcripción que demuestre la mayor probabilidad de ser precisa y representativa de un intercambio auténtico, dando preferencia a las que sigan la estructura indicativo + comando + valor.

# Formato de Salida

La salida debe ser la transcripción seleccionada, presentada de forma literal como texto plano, sin ninguna alteración. SOLO LA TRANSCRIPCIÓN SELECCIONADA, NADA MÁS.

# Vocabulario típico

{PROMPT_ES}

# Nombres de Aerolíneas

- aegean
- aeroflot
- air algerie
- aireuropa
- air nostrum
- air portugal
- airfrans
- albastar
- alpine
- babcock
- bee-line
- belstar
- binter
- bluebird
- bluefin
- bluescan
- braathens
- britannia
- british
- speedbird
- caledonian
- canair
- canary
- channex
- clickair
- condor
- cygnus
- cyprus
- dagobert
- dahl
- danish
- delta
- denim
- easy
- edelweiss
- egyptair
- eurotransit
- eurowings
- evelop
- finnair
- fraction
- france soleil
- gestair
- griffin
- iberia
- iberiaexpress
- iceair
- japanair
- klm
- lufthansa
- lufthansa cargo
- luxair
- nor shuttle
- privilege
- postman
- qantas
- quality
- royalair maroc
- ryanair
- shamrock
- singapore
- swiss
- topswiss
- tuijet
- tunair
- virgin
- volotea
- vueling
- wizzair
- zorex

# Ciudades

- Sídney
- Tokio
- Nueva York
- Londres
- París
- Roma
- Berlín
- Madrid
- Barcelona
- Dubái
- Hong Kong
- Los Ángeles
- Toronto
- Singapur
- San Francisco
- Ciudad de México
- Buenos Aires
- Ciudad del Cabo
- Moscú
- Pekín
- Seúl
- Ámsterdam
- Viena
- Bangkok
- Estambul
- Río de Janeiro
- Bombay
- El Cairo
- Melbourne
- Atenas

# Transcripciones
""".strip()


def jaccard_distance(str1, str2):
    """
    Calcula la distancia de Jaccard entre dos cadenas de texto.

    Args:
        str1 (str): Primera cadena de texto.
        str2 (str): Segunda cadena de texto.

    Returns:
        float: Distancia de Jaccard entre las dos cadenas.
    """

    set1 = set(str1.split())
    set2 = set(str2.split())
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return 1 - (intersection / union if union > 0 else 0)

class AgentState(TypedDict):
    """
    Define el estado para el agente, incluyendo mensajes, ruta de audio, mejor transcripción,
    todas las transcripciones y el recuento de revisiones.
    """
    messages: Annotated[list[AnyMessage], operator.add]
    audio_path: str
    best_transcript: str
    all_transcripts: list
    check_correctness: bool


class TranscriptionAgent:
    """
    Agente encargado de transcribir y seleccionar la mejor transcripción de conversaciones
    entre un controlador aéreo y un piloto utilizando modelos de Whisper y LLM.
    """

    def __init__(self, model_name: str):
        """
        Inicializa el agente de transcripción.

        Args:
            model_name (str): Nombre del modelo de lenguaje a utilizar con OllamaLLM.
        """
        self.init_whisper()
        self.llm = OllamaLLM(model=model_name, temperature=0.0, top_k=1)

        # Crear un grafo para gestionar las transiciones de estado del agente
        graph = StateGraph(AgentState)
        graph.add_node('whisper', self.transcribe)  # Añadir nodo de transcripción
        graph.add_node('selector', self.select_transcript)  # Añadir nodo de selección de transcripción
        graph.add_node('whisper_deterministic', self.transcribe_deterministic)  # Nodo de transcripción determinística

        # Definir transición condicional basada en la comparación de transcripciones
        graph.add_conditional_edges('whisper', self.check_identical_transcripts, path_map={True: END, False: 'selector'}) # Check identical transcripts
        graph.add_conditional_edges('selector', self.check, path_map={True: END, False: 'whisper_deterministic'}) # Check correctness
        graph.add_edge('whisper_deterministic', END)  # Añadir transición final

        graph.set_entry_point("whisper")  # Establecer el punto de entrada del grafo
        self.graph = graph.compile()

    def init_whisper(self):
        """
        Inicializa el modelo y el procesador de Whisper para la transcripción de audio.
        """
        MODEL_NAME = "jlvdoorn/whisper-large-v3-atco2-asr"


        # Establecer el tipo de dispositivo (GPU o CPU) según la disponibilidad
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            self.dtype = torch.float16
        else:
            self.device = torch.device("cpu")
            self.dtype = torch.float32

        # Cargar el modelo y el procesador de Whisper
        self.whisper = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME).to(self.device)
        self.whisper_processor = WhisperProcessor.from_pretrained(MODEL_NAME)


    def invoke(self, audio_path: str, normalize: bool , language: str = None):
        """
        Invoca el proceso de transcripción y selección de transcripción.

        Args:
            audio_path (str): Ruta al archivo de audio a transcribir.
            normalize (bool): Indica si se debe normalizar la transcripción.
            language (str, optional): Código del idioma del audio ('en' o 'es'). Para detección automática dejarlo vacío.

        Returns:
            dict: Estado actualizado después de la invocación.
        """
        if not os.path.exists(audio_path):
            return
        elif os.path.splitext(audio_path)[1] not in ALLOWED_EXTENSIONS:
            return

        if normalize == None:
            return
        
        self.normalize = normalize

        if language not in ALLOWED_LANGUAGES:
            return

        self.language = language

        result = self.graph.invoke({'audio_path': audio_path})
        return result['best_transcript']

    def split_audio(self, audio_path, max_duration=30, target_sr=16000):
        """
        Divide un archivo de audio en fragmentos de máximo `max_duration` segundos.
        
        Args:
            audio_path (str): Ruta del archivo de audio.
            max_duration (int): Duración máxima en segundos de cada fragmento.
            target_sr (int): Frecuencia de muestreo objetivo.
        
        Returns:
            list: Lista de fragmentos de audio.
        """
        audio, sr = load(audio_path, sr=target_sr)
        samples_per_segment = max_duration * sr
        segments = [audio[i:i + samples_per_segment] for i in range(0, len(audio), samples_per_segment)]
    
        return segments, sr
    
    def transcribe(self, state: AgentState):  
        """
        Transcribe un audio completo en segmentos de 30 segundos y genera múltiples transcripciones.

        Args:
            state (AgentState): Estado actual del agente.

        Returns:
            dict: Estado actualizado con todas las transcripciones y la mejor inicialmente.
        """
        
        if self.language == 'es':
            PROMPT = PROMPT_ES
        else:
            PROMPT = PROMPT_NEW_EN
        
        self.whisper_prompt = PROMPT

        # Dividir el audio en fragmentos de máximo 30 segundos
        audio_segments, sr = self.split_audio(state['audio_path'], max_duration=30)

        all_transcripts = []  # Guardará las transcripciones completas de cada variante
        best_transcription = []  # La mejor transcripción unida en un solo string

        # Crear una lista para almacenar transcripciones por cada variación generada
        num_variants = 5  # Cuántas transcripciones generamos por cada segmento
        transcript_variants = [[] for _ in range(num_variants)]  

        for segment in audio_segments:
            input_features = self.whisper_processor(
                audio=segment,
                return_tensors="pt",
                sampling_rate=sr,
                device=self.device
            ).input_features
            input_features = input_features.to(self.device)

            # Crear una máscara de atención
            attention_mask = (input_features != 0).float()

            # Precomputar los IDs del prompt
            self.prompt_ids = self.whisper_processor.get_prompt_ids(self.whisper_prompt, return_tensors="pt").to(self.device)

            # Generar múltiples transcripciones (usando beam search)
            with torch.no_grad():
                pred_ids = self.whisper.generate(
                    input_features,
                    prompt_ids=self.prompt_ids,
                    attention_mask=attention_mask,
                    num_beams=num_variants,  # Generar 5 transcripciones distintas
                    num_return_sequences=num_variants,
                    early_stopping=True,
                    temperature=0.5,
                    language=self.language,
                    task="transcribe"
                )

            # También generamos una versión determinista (temp=0)
            with torch.no_grad():
                pred_ids_det = self.whisper.generate(
                    input_features,
                    prompt_ids=self.prompt_ids,
                    attention_mask=attention_mask,
                    temperature=0.0,
                    language=self.language,
                    task="transcribe"
                )

            # Decodificar la mejor transcripción (determinista)
            decoded_det = self.whisper_processor.decode(pred_ids_det[0], skip_special_tokens=True, language=self.language)
            if self.normalize:
                decoded_det = filterAndNormalize(decoded_det)
            
            best_transcription.append(decoded_det)  # Agregamos al texto final

            # Decodificar las variantes y agregarlas en la posición correspondiente
            for i, beam_output in enumerate(pred_ids):
                decoded = self.whisper_processor.decode(beam_output, skip_special_tokens=True, language=self.language)
                if self.normalize:
                    decoded = filterAndNormalize(decoded)
                transcript_variants[i].append(decoded)

        # Unimos las transcripciones por variante
        all_transcripts = [" ".join(variant) for variant in transcript_variants]

        # Unir la mejor transcripción de cada segmento en un solo texto
        final_best_transcription = " ".join(best_transcription)

        # Crear un mensaje con todas las transcripciones para revisión
        message_content = '\n'.join([f"{i+1}. {t}" for i, t in enumerate(all_transcripts)])
        message = HumanMessage(content=message_content)

        return {
            'messages': [message],
            'all_transcripts': all_transcripts,  # Lista con las diferentes transcripciones completas
            'best_transcript': final_best_transcription  # Mejor transcripción final
        }

    def check_identical_transcripts(self, state: AgentState):
        """
        Verifica si todas las transcripciones generadas son idénticas.

        Args:
            state (AgentState): Estado actual del agente.

        Returns:
            bool: True si todas las transcripciones son idénticas, False en caso contrario.
        """
        transcripts = state['all_transcripts']
        if len(transcripts) == 0:
            identical = False
        else:
            reference = transcripts[0]
            identical = all(reference == t for t in transcripts)

        return identical

    def select_transcript(self, state: AgentState):
        """
        Selecciona la mejor transcripción utilizando un modelo de lenguaje.

        Args:
            state (AgentState): Estado actual del agente.

        Returns:
            dict: Estado actualizado con la transcripción seleccionada.
        """
        # Seleccionar el prompt del sistema según el idioma
        system_prompt = SYSTEM_PROMPT_ES if self.language == 'es' else SYSTEM_PROMPT_EN

        # Añadir el prompt del sistema y la solicitud del usuario a los mensajes
        messages = state['messages']
        messages = messages + [SystemMessage(content=system_prompt), HumanMessage(content="Select the best transcript")]
        # Invocar el LLM para seleccionar la mejor transcripción
        message_content = self.llm.invoke(messages)
        message = AIMessage(content=message_content)

        # Devolver el estado actualizado con la transcripción seleccionada
        return {'messages': [message], 'best_transcript': message.content}

    def check(self, state: AgentState):
        """
        Verifica si la transcripción seleccionada contiene errores claros.

        Args:
            state (AgentState): Estado actual del agente.

        Returns:
            dict: Estado actualizado con la transcripción seleccionada.
        """

        check = True
        best_transcript = state['best_transcript']
        max_desviation = 1
        max_jaccard_distance = 0.3
        min_distance = min(jaccard_distance(best_transcript, t) for t in state['all_transcripts'])

        if (len(best_transcript.split()) > max(len(t.split()) + max_desviation for t in state['all_transcripts']) or
            len(best_transcript.split()) < min(len(t.split()) - max_desviation for t in state['all_transcripts'])):
            check = False
        elif min_distance > max_jaccard_distance:
            check = False

        return check

    def transcribe_deterministic(self, state: AgentState):
        """
        Transcribe el audio proporcionado y genera una única transcripción.

        Args:
            state (AgentState): Estado actual del agente.

        Returns:
            dict: Estado
        """

        all_transcripts = state['all_transcripts']

        message = HumanMessage(content=f"Deterministic Transcript:\n{all_transcripts[0]}")
    
        return {'messages': [message], 'all_transcripts': all_transcripts, 'best_transcript': all_transcripts[0]}

# Instancia global de TranscriptionAgent
transcriber_instance = TranscriptionAgent(model_name=settings.OLLAMA_MODEL)