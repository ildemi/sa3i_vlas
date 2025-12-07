"""
This module provides functionality for invoking a graph with conversational input data
and saving the resulting output. It is designed to process conversations between roles such 
as 'pilot' and 'ATCO' (air traffic control), evaluate various aspects of the communication 
like phraseology and collation, and store the results for further analysis.
"""

import os, json
from .utils.utils import *
from .utils.prompts import *
from .utils.logger_config import logger
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama


class Phrase:
    """
    A class representing a single phrase spoken by a specific speaker in a conversation.

    This class stores information about the speaker, the associated rule, the phrase content, 
    and tracks any validation failures related to the phrase. It also maintains supervision 
    information to guide further checks and corrections.

    Attributes:
        speaker (str): The role or identity of the speaker (e.g., 'pilot', 'ATCO').
        text (str): The actual phrase spoken by the speaker.
        rule (str): The rule of the phraseology associated with the phrase.
        callSignFailure (str): Stores an explanation if there is a callsign failure.
        phraseologyFails (str): Stores the phraseology-related issues with the phrase.
        otherPhraseology (bool): Indicates if the phrase does not follow the standard phraseology (True if non-standard, False if standard).
        supervised (dict): Dictionary tracking the supervision state, including a counter for rechecks and an explanation.
    """
    def __init__(self, speaker: str, text: str):
        """
        Initializes a new Phrase instance with the given speaker, rule, and text.

        Args:
            speaker (str): The role or identity of the speaker (e.g., 'pilot', 'ATCO').
            text (str): The actual phrase spoken by the speaker.
        """
        self.speaker = speaker
        self.text = text
        self.rule = ''
        self.callSignFailure = ''
        self.phraseologyFails = ''
        self.otherPhraseology = False
        self.supervised = {'counter': 0, 'checkAgain': True, 'explanation': ''}

    def __str__(self) -> str:
        return f'Speaker: {self.speaker}. Phrase: {self.text}. Rule: {self.rule}. Minor fails: {self.phraseologyFails}. Supervised: {self.supervised}'

class AgentState(TypedDict):
    """
    A dictionary-like class used to store the state of the graph and validation process.

    This class is designed to track the status of a conversation as it is processed through a validation graph. 
    It stores the input data, the phrases being analyzed, and the results of validation checks related to various 
    aspects of the communication, including language errors, collation issues, and callsign inconsistencies.

    Attributes:
        input (list[tuple]): A list of tuples where each tuple represents a speaker and their corresponding phrase.
        phrases (list[Phrase]): A list of `Phrase` objects that hold the details of the conversation phrases.
        checkAgain (bool): Flag indicating whether the conversation should be checked again.
        language_error (str): A string indicating any language-related errors.
        collation_error (dict): Dictionary tracking the supervision state with a string indicating any collation errors (e.g., missing or incorrect information).
        score (dict): A dictionary storing scores or results related to the validation process.
        next (str): Indicates the next node in the supervisor loop.
    """
    input: list[tuple]
    phrases: list[Phrase]
    checkAgain: bool
    language_error: str
    collation_error: dict
    score: dict
    next: str

class Validator:
    """
    A class responsible for validating various aspects of communication between roles, such as 'pilot' and 'ATCO'.
    
    This class processes conversational data, checks for rule compliance, and evaluates errors in aspects like 
    phraseology, collation, call signs, and language usage. It is primarily used in the context of air traffic control 
    communications but can be applied to any dialogue where specific rules need to be enforced.

    The class provides methods for invoking validation checks, generating outputs based on the analysis of the conversation, 
    and saving the results.

    Attributes:
        model: The model used to process and validate the conversational data.

    Methods:
        invoke(input: list[tuple[str, str]]): Validates the conversation data, processes it through the graph model, 
                                               and stores the output.
    
    Usage:
        1. Create an instance of the Validator class.
        2. Provide a list of tuples representing the conversation (role, phrase).
        3. Call the `invoke` method to validate the conversation.
        4. The validation results will be saved automatically.

    Example:
        validator = Validator(model='llama3.1')
        input_data = [('pilot', 'Requesting permission for takeoff'), ('atco', 'Cleared for takeoff')]
        validator.invoke(input_data)
    """

    def __init__(self, model: str, validateOnlyPhraseology: bool = False):
        """
        Initializes the Validator class with a specified model for validation.

        Args:
            model (str): The name or identifier of the model to be used for validation. 
            validateOnlyPhraseology (bool): Flag indicating whether to validate only phraseology (default is False).
        """
        self.model = ChatOllama(model=model, temperature=0.1)
        self.validateOnlyPhraseology = validateOnlyPhraseology
        self.errors_summary = ""
        self.result = {}

        # Load phraseology
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.rules = getRules(os.path.join(current_dir, 'utils', 'phraseology.md'))

        # Add nodes
        builder = StateGraph(AgentState)
        builder.add_node('identify_rule', self.__identifyRule)
        builder.add_node('check_collation', self.__checkCollation)
        builder.add_node('check_callsign', self.__checkCallSign)
        builder.add_node('check_language', self.__checkLanguage)
        builder.add_node('check_phraseology', self.__checkPhraseology)
        builder.add_node('supervisor', self.__supervisor)
        builder.add_node('check_other_phraseology', self.__checkOtherPhraseology)
        builder.add_node('scorer', self.__scorer)

        builder.add_edge(START, 'identify_rule')
        builder.add_edge('identify_rule', 'check_language')
        builder.add_edge('check_language', 'check_collation')

        self.need_supervisor = ['check_collation', 'check_callsign', 'check_phraseology']
        conditional_map = {k: k for k in self.need_supervisor}
        conditional_map["FINISH"] = 'check_other_phraseology'

        for member in self.need_supervisor:
            builder.add_edge(member, "supervisor")

        builder.add_conditional_edges("supervisor", self.__shouldContinue, conditional_map)
        
        builder.add_edge('check_other_phraseology', 'scorer')
        builder.add_edge('scorer', END)

        # Compile the graph
        self.graph = builder.compile()


    def __cleanOutput(self, response: str):
        """
        Cleans and parses the response content, extracting and converting the JSON block into a Python dictionary.
        This method processes the raw response, identifies the JSON block within the content, and attempts to parse it
        into a Python dictionary. It removes any unwanted formatting or text outside the JSON block.
        Args:
            response (str): The response string containing the raw content to be cleaned. 
                            It is expected to have a `content` attribute which holds the response data.
        Returns:
            dict: A cleaned and parsed dictionary representation of the response content, if successful.
        """

        cleanedResponse = {}
        try:
            # Busca el primer bloque JSON en la respuesta
            json_match = re.search(r'{.*?}', response.content.strip(), re.DOTALL)
            if json_match:
                json_block = json_match.group(0)  # Captura el bloque JSON
                
                # Eliminar la coma final, si existe, antes de parsear
                json_block = re.sub(r',\s*}', '}', json_block)
                
                # Asegurar que las claves del JSON tengan comillas dobles
                # Buscar patrones como {Clave} o {Clave:} y reemplazarlos con {"Clave"}
                json_block = re.sub(r'{([^{}"\']+?)(:|\s*})', r'{"\1"\2', json_block)
                # Buscar patrones como ,Clave: y reemplazarlos con ,"Clave":
                json_block = re.sub(r',\s*([^{}"\']+?):', r',"\1":', json_block)
                
                # Parsear el JSON
                try:
                    cleanedResponse = json.loads(json_block)
                    logger.debug(f'Response: {cleanedResponse}')
                except json.JSONDecodeError as jde:
                    # Si todavía hay error, intentar una limpieza más agresiva
                    logger.warning(f"First attempt failed: {jde}. Trying more aggressive cleaning.")
                    # Forzar formato JSON correcto para claves sin comillas
                    json_block = re.sub(r'([{,])\s*([^{},:"\']+?)\s*:', r'\1"\2":', json_block)
                    cleanedResponse = json.loads(json_block)
                    logger.debug(f'Response after aggressive cleaning: {cleanedResponse}')
            else:
                logger.warning(f"No valid JSON block found in the content: {response.content}")
        except json.JSONDecodeError as jde:
            logger.error(f"JSON decoding error: {jde}")
            logger.error(f"Extracted block: {json_block}")
        except Exception as e:
            logger.exception(f"Unexpected error while extracting or parsing JSON: {e}")

        return cleanedResponse

    def __normalizeRule(self, rule_text: str):
        """Normalizes the rule text by removing extra spaces, converting to lowercase, removing all symbols,
        removing accents, and reducing internal whitespace to single spaces. This helps ensure consistent comparisons between
        similar rule strings.

        Args:
            rule_text (str): The rule text to be normalized.

        Returns:
            str: A cleaned, lowercase version of the rule text with symbols removed, accents removed, and extra whitespace reduced.
        """
        # Remove accents
        rule_text = rule_text.lower()
        rule_text = re.sub(r'[áàäâ]', 'a', rule_text)
        rule_text = re.sub(r'[éèëê]', 'e', rule_text)
        rule_text = re.sub(r'[íìïî]', 'i', rule_text)
        rule_text = re.sub(r'[óòöô]', 'o', rule_text)
        rule_text = re.sub(r'[úùüû]', 'u', rule_text)
        rule_text = re.sub(r'ñ', 'n', rule_text)

        # Remove all symbols, keep only alphanumeric characters and spaces
        cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', rule_text)
        # Normalize spaces and convert to lowercase
        return re.sub(r'\s+', ' ', cleaned_text.strip())


    def __identifyRule(self, state: AgentState):
        """
        Identifies the rule associated with the conversation phrases based on the phraseology.

        This method processes the input data in the provided `AgentState`, analyzing each conversation phrase 
        and comparing it with predefined rules. The method attempts to identify the most relevant rule 
        for each phrase by calculating phrase similarities and interacting with a model to retrieve the rule. 
        The identified rules are then stored in `Phrase` objects for further validation.
        """
        logger.info('Identifying rules')
        state['phrases'] = [Phrase(speaker=entry[0], text=entry[1]) for entry in state['input']]

        for phrase in state['phrases']:
            logger.debug(f'Phrase: {phrase.text}')

            # Identify language of the phrase
            response = self.model.invoke([HumanMessage(content=f'{prompt_language_detection}\n {phrase.text}')])
            response = self.__cleanOutput(response)
            language = response.get('language', '')

            # Calculate top similarities rules
            top_rules, _ = calculate_top_similarities(phrase.text, self.rules, language)
            
            if len(top_rules) > 0:
                # Select the most similar rule with the LLM
                prompt = f'INSTRUCCIONES:\n {promptIdentifyFilteredRules}\n {phrase.text}\nFRASEOLOGÍA:\n {top_rules}'
                response = self.model.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
                response = self.__cleanOutput(response)
                rule = response.get('rule', '')

                # Normalize the rule and the top rules for comparison
                normalized_rule = self.__normalizeRule(rule)
                normalized_top_rules = [self.__normalizeRule(top_rule) for top_rule in top_rules]

                if response.get('rule_exists') == False or normalized_rule not in normalized_top_rules:
                    # Rule does not exist or is not in the top rules
                    top_rule, score = calculate_top_similarities(phrase.text, self.rules, language, top_n=1)
                    if score[0] > 0.60:
                        logger.debug(f"Top rule: {top_rule[0]} with score: {score[0]}")
                        phrase.rule = top_rule[0]
                    else:
                        phrase.otherPhraseology = True
                else:          
                    # Rule exists and is in the top rules
                    phrase.rule = rule
            else:
                # No rules found
                logger.debug(f'La frase no coincide con ninguna regla: {phrase.text}')
                phrase.otherPhraseology = True

            if phrase.otherPhraseology == True:
                phrase.rule = 'No se ha encontrado ninguna regla en la fraseología que coincida con la frase'
        
        return {'phrases': state['phrases']}

    def __checkLanguage(self, state: AgentState):
        """
        Checks the language usage in the conversation data to ensure that the communication follows the correct language rules.

        This method processes the conversation's phrases and evaluates whether multiple languages are used 
        correctly according to the specified rules. It checks for any violations of language mixing and verifies 
        that the language used is appropriate for the context.
        """
        logger.info('Checking language')
        conversation = "\n".join([f"{role.upper()}: {message}" for role, message in state['input']])
        logger.debug(conversation)

        prompt = f'INSTRUCCIONES:\n{promptCheckLanguage}\n Conversacion: {conversation}'

        response = self.model.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
        response = self.__cleanOutput(response)
        if response.get('can_mix') == False and response.get('is_correct') == False:
            return {'language_error': response.get('explanation')}

        return {'language_error': 'El uso del lenguaje es correcto'}   
    
    def __checkCollation(self, state: AgentState):
        """
        Checks the collation of the conversation data to ensure it adheres to the expected rules.

        This method processes the conversation data in the provided `AgentState`, checks if collation is needed 
        based on the conversation's content, and if required, further validates the correctness of the collation. 
        The method interacts with the model to assess collation issues and provides an explanation if any errors are found.
        """
        logger.info('Checking collation')
        conversation = "\n".join([f"{role.upper()}: {message}" for role, message in state['input']])
        logger.debug(conversation)
        collation_state = state['collation_error']

        if collation_state['counter'] > 0:
            prompt = f"INSTRUCCIONES:\n{promptCheckAgainCollation}\n Conversacion: {conversation}\n Evaluación anterior: {collation_state['explanation']}\nEvaluación del supervisor: {collation_state['supervisor_explanation']}"
            response = self.model.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
            response = self.__cleanOutput(response)
            collation_state['explanation'] = response.get('explanation')

            return {'collation_error': collation_state, 'next': 'check_collation'}

        prompt = f'\nINSTRUCCIONES:\n {promptNeedCollation}\n {conversation}'
        response = self.model.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
        response = self.__cleanOutput(response)

        if response.get('needCollation') == True:
            prompt = f'\nINSTRUCCIONES:\n {promptCheckCollation}\n {conversation}'
            response = self.model.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
            response = self.__cleanOutput(response)
            collation_state['explanation'] = response.get('explanation')

            return {'collation_error': collation_state, 'next': 'check_collation'}
        
        return {'collation_error': {'explanation': 'No aplica'}, 'next': 'check_collation'}

    def __checkCallSign(self, state: AgentState):
        """
        Checks the consistency of call signs in the conversation data.

        This method processes the conversation's phrases and examines any references to call signs. 
        It checks if the call signs are used correctly according to the specified rules and identifies any inconsistencies 
        in their usage. The method interacts with the model to verify the validity of each call sign and provides 
        an explanation if an error is found.
        """
        logger.info('Checking call sign')

        for phrase in state['phrases']:
            if 'distintivo de llamada' in phrase.rule or 'call sign' in phrase.rule:
                if phrase.supervised['counter'] == 0:
                    prompt = f'INSTRUCCIONES:\n{promptCheckCallSign}\n Regla: {phrase.rule}\n Frase: {phrase.text}'
                elif phrase.supervised['checkAgain'] == True:
                    prompt = f"INSTRUCCIONES:\n{promptCheckAgainCallSign}\n Regla: {phrase.rule}\n Frase: {phrase.text}\nEvaluación anterior: {phrase.callSignFailure}\nEvaluación del supervisor: {phrase.supervised['explanation']}"
                else:
                    continue
                logger.debug(f'Text: {phrase.text}. Rule: {phrase.rule}')
                response = self.model.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
                response = self.__cleanOutput(response)

                if response.get('correct_call_sign') == False:
                    phrase.callSignFailure = response.get('explanation')
                else:
                    phrase.callSignFailure = 'Correcto'
            elif phrase.otherPhraseology == False:
                phrase.callSignFailure = 'No requiere call sign'

        return {'phrases': state['phrases'], 'next': 'check_callsign'}  

    def __checkPhraseology(self, state: AgentState):
        """
        Checks if each phrase in the conversation follows the standard phraseology rules.

        This method iterates over the list of phrases in the conversation state, validating each phrase
        against predefined phraseology rules. If a phrase fails the initial validation, it records the 
        explanation of the failure. For phrases flagged for re-evaluation, it runs additional checks based 
        on prior corrections from the supervisor that need to be applied.
        """
        logger.info('Checking phraseology')

        for phrase in state['phrases']:
            if phrase.otherPhraseology == False:
                if phrase.supervised['counter'] == 0:
                    prompt = f'INSTRUCCIONES:\n{promptCheckPhraseology}\n Regla: {phrase.rule}\n Conversacion: {phrase.text}'
                elif phrase.supervised['checkAgain'] == True:
                    prompt = f"INSTRUCCIONES:\n{promptCheckAgainPhraseology}\n Regla: {phrase.rule}\n Conversacion: {phrase.text}\nEvaluación anterior: {phrase.phraseologyFails}\nEvaluación del supervisor: {phrase.supervised['explanation']}"
                else:
                    continue

                logger.debug(f'Text: {phrase.text}. Rule: {phrase.rule}')
                response = self.model.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
                response = self.__cleanOutput(response)
                phrase.phraseologyFails = response.get('explanation')

        return {'phrases': state['phrases'], 'next': 'check_phraseology'}

    def __supervisor(self, state: AgentState):
        """
        Supervises the validation results from the self.need_supervisors nodes, ensuring that evaluations from the llm are correct.
        If an evaluation is marked as incorrect, it provides feedback and flag it for re-evaluation.
        This process iterates until all phrases are correctly evaluated or the supervision limit is reached.
        """
        logger.info('Supervising')
        checkAgain = False

        if state['next'] == 'check_phraseology':
            for phrase in state['phrases']:
                if phrase.otherPhraseology == False and phrase.supervised['checkAgain'] == True:
                    prompt = f'INSTRUCCIONES:\n{promptSupervisorPhraseology}\n Regla: {phrase.rule}\n Conversacion: {phrase.text}\n Evaluacion del llm: {phrase.phraseologyFails}'
                    logger.debug(f'Text: {phrase.text}. Rule: {phrase.rule}. Evaluacion anterior: {phrase.phraseologyFails}')
                    response = self.model.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
                    response = self.__cleanOutput(response)

                    phrase.supervised['counter'] += 1
                    phrase.supervised['explanation'] = response.get('explanation')

                    if response.get('is_correct') == False and phrase.supervised['counter'] < 5:
                        checkAgain = True
                        phrase.supervised['checkAgain'] = True
                    else:
                        phrase.supervised['checkAgain'] = False

            if checkAgain == False:
                for phrase in state['phrases']:
                    phrase.supervised = {'counter': 0, 'checkAgain': True, 'explanation': ''}
            return {'checkAgain': checkAgain, 'phrases': state['phrases']}

        elif state['next'] == 'check_callsign':
            for phrase in state['phrases']:
                if ('distintivo de llamada' in phrase.rule or 'call sign' in phrase.rule) and phrase.supervised['checkAgain'] == True:
                    prompt = f'INSTRUCCIONES:\n{promptSuperviseCallSign}\n Regla: {phrase.rule}\n Frase: {phrase.text}\n Evaluacion del llm: {phrase.callSignFailure}'
                    logger.debug(f'Text: {phrase.text}. Rule: {phrase.rule}. Evaluacion anterior: {phrase.callSignFailure}')
                    response = self.model.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
                    response = self.__cleanOutput(response)

                    phrase.supervised['counter'] += 1
                    phrase.supervised['explanation'] = response.get('explanation')

                    if response.get('is_correct') == False and phrase.supervised['counter'] < 5:
                        checkAgain = True
                        phrase.supervised['checkAgain'] = True
                    else:
                        phrase.supervised['checkAgain'] = False

            if checkAgain == False:
                for phrase in state['phrases']:
                    phrase.supervised = {'counter': 0, 'checkAgain': True, 'explanation': ''}            
            return {'checkAgain': checkAgain, 'phrases': state['phrases']}
        
        elif state['next'] == 'check_collation':
            collation_state = state['collation_error']
            if collation_state['explanation'] != 'No aplica':
                conversation = "\n".join([f"{role.upper()}: {message}" for role, message in state['input']])
                logger.debug(f"Conversacion: {conversation}.\nEvaluacion del llm: {collation_state['explanation']}")

                prompt = f"\nINSTRUCCIONES:\n {promptSuperviseCollation}\n Conversación: {conversation} Evaluacion del llm: {collation_state['explanation']}"
                response = self.model.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
                response = self.__cleanOutput(response)
                
                collation_state['counter'] += 1
                if response.get('is_correct') == False and collation_state['counter'] < 5:
                    checkAgain = True
                    collation_state['supervisor_explanation'] = response.get('explanation')
            return {'checkAgain': checkAgain, 'collation_error': collation_state}

        return {'checkAgain': checkAgain}

    def __shouldContinue(self, state: AgentState):
        """
        Evaluates whether the validation process should proceed based on the current state of the conversation.
        The function checks if the validation needs to be repeated, if the current validation step is the last one, 
        or if the next step in the process should be executed.
        """

        if state['checkAgain'] == True:
            # Si necesita otra revision se vuelve a llamar al mismo nodo
            return state['next']

        elif state['next'] == self.need_supervisor[-1]:
            # No necesita mas revisiones y ya es el ultimo nodo
            return 'FINISH'
        else:
            # Avanza a la siguiente posición en la lista self.need_supervisor
            next_index = self.need_supervisor.index(state['next']) + 1
            return self.need_supervisor[next_index]

    def __checkOtherPhraseology(self, state: AgentState):
        """
        Evaluates phrases that do not conform to the standard phraseology.

        This function provides an assessment for phrases within the `AgentState` that have already been 
        identified as deviating from the standard phraseology. It records relevant details about these 
        non-standard phrases for reporting and further validation purposes.
        """
        logger.info('Checking other phraseology')
        conversation = "\n".join([f"{role.upper()}: {message}" for role, message in state['input']])

        for phrase in state['phrases']:
            if phrase.otherPhraseology == True:
                prompt = f'INSTRUCCIONES:\n{promptCheckOtherPhraseology}\n Frase: {phrase.text} Conversacion entera: {conversation}'
                logger.debug(f'Text: {phrase.text}.')
                response = self.model.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
                response = self.__cleanOutput(response)
                phrase.phraseologyFails = response.get('explanation')

        return {'phrases': state['phrases']}

    def __scorer(self, state: AgentState):
        """
        Evaluates the errors in the conversation and assigns a score based on the validation results.

        This method compiles a summary of the errors detected in the conversation, including language errors, collation errors, 
        global failures, and inconsistencies with callsigns. It also evaluates each phrase in the conversation, 
        noting any issues related to callsigns or phraseology. Finally, it generates a prompt with the summarized errors and 
        sends it to the model to obtain a score for the conversation.
        """
        logger.info('Putting score')
        logger.debug(state)
        self.errors_summary = ''
        
        # Evaluación de los errores de lenguaje
        if state.get('language_error'):
            self.errors_summary += f"- Mezcla de idiomas: {state['language_error']}\n"

        # Evaluación de errores de colación
        if state.get('collation_error').get('explanation'):
            self.errors_summary += f"- Colación: {state['collation_error']['explanation']}\n"

        # Evaluación de las frases revisadas
        for phrase in state['phrases']:
            self.errors_summary += f"\nFrase: \"{phrase.text}\" (de {phrase.speaker})\n"
            self.errors_summary += f"  Regla aplicada: {phrase.rule}\n"
            if phrase.callSignFailure:
                self.errors_summary += f" Callsign: {phrase.callSignFailure}\n"
            if phrase.otherPhraseology == True:
                self.errors_summary += f"  Fraseologia: Evaluación del llm: {phrase.phraseologyFails}\n"
            else:
                self.errors_summary += f"  Fraseologia: {phrase.phraseologyFails}\n"
            
        conversation = "\n".join([f"{role.upper()}: {message}" for role, message in state['input']])
        scores = {}

        prompt = f"iNSTRUCCIONES:\n{promptScoreLanguage}\nConversacion:{conversation}\nErrores encontrados:\n{state['language_error']}"
        response = self.model.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
        scores['mezcla_idiomas'] = self.__cleanOutput(response)

        prompt = f"iNSTRUCCIONES:\n{promptScoreCollation}\nConversacion:{conversation}\nErrores encontrados:\n{state['collation_error']['explanation']}"
        response = self.model.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
        scores['colacion'] = self.__cleanOutput(response)
        
        for category, prompt in [('fraseologia', promptScorePhraseology), ('call_signs', promptScoreCallsigns), ('puntuacion_piloto', promptScorePilot), ('puntuacion_atco', promptScoreAtco), ('puntuacion_total', promptScoreTotal)]:
            prompt = f"iNSTRUCCIONES:\n{prompt}\nConversacion:{conversation}\nLista de errores encontrados:\n{self.errors_summary}"
            response = self.model.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
            scores[category] = self.__cleanOutput(response)

        #TODO Añadir valoracion de gravedad de los errores
        return {'score': scores}

    def serialize_result(self):
        """
        Serializa el resultado del validador para que sea compatible con JSON.
        
        Convierte los objetos Phrase y otros datos no serializables a diccionarios
        y tipos de datos básicos que son serializables a JSON.
        
        Returns:
            dict: Versión serializable del resultado de la validación
        """
        serialized = {}
        
        # Serializar los atributos generales
        if 'language_error' in self.result:
            serialized['language_error'] = self.result['language_error']
        
        if 'collation_error' in self.result:
            serialized['collation_error'] = {
                'explanation': self.result['collation_error'].get('explanation', ''),
                'counter': self.result['collation_error'].get('counter', 0),
                'supervisor_explanation': self.result['collation_error'].get('supervisor_explanation', '')
            }
        
        # Serializar las frases
        if 'phrases' in self.result:
            serialized['phrases'] = []
            for phrase in self.result['phrases']:
                serialized_phrase = {
                    'speaker': phrase.speaker,
                    'text': phrase.text,
                    'rule': phrase.rule,
                    'callSignFailure': phrase.callSignFailure,
                    'phraseologyFails': phrase.phraseologyFails,
                    'otherPhraseology': phrase.otherPhraseology,
                    'supervised': phrase.supervised
                }
                serialized['phrases'].append(serialized_phrase)
        
        # Serializar las puntuaciones
        if 'score' in self.result:
            serialized['score'] = self.result['score']
        
        # Incluir el resumen de errores
        serialized['errors_summary'] = self.errors_summary
        
        return serialized

    def invoke(self, input: list[tuple[str, str]]):
        """
        Invokes the graph with the provided input and saves the output.

        This method takes a list of tuples where each tuple contains the role of the speaker 
        (e.g., 'pilot' or 'atco') and the corresponding phrase they said. It processes the input
        through the graph and stores the result.

        If the `validateOnlyPhraseology` flag is `False`, the result is saved to a file. If it is `True`, only the phraseology validation is performed.

        Args:
            input (list[tuple[str, str]]): A list of tuples where each tuple consists of:
                - str: The role of the speaker (e.g., 'pilot', 'atco').
                - str: The phrase spoken by that person.

        Returns:
            - If `validateOnlyPhraseology` is `False`, returns a serialized version of the validation result.
            - If `validateOnlyPhraseology` is `True`, returns the result of the phraseology check as a list of phrases and their phraseology status.
        """
        input = [(role.lower(), phrase.lower()) for role, phrase in input]
        self.result = self.graph.invoke({'input': input, 'collation_error': {'counter': 0, 'explanation': '', 'supervisor_explanation': ''}}, {'recursion_limit': 40})

        if self.validateOnlyPhraseology == False:
            self.saveToFile()
            return self.serialize_result()
        else:
            return self.followPhraseology()

    def saveToFile(self):
        """
        Saves the conversation, errors, and scores to a log file for later review.

        This function opens a log file in append mode and writes the following information:
        1. The conversation, iterating through each phrase and writing the speaker and text.
        2. A summary of errors that occurred during the validation.
        3. The scores for different categories, including explanations.

        The log is saved to the file located at 'files/logs/output.log', and the function logs an informational message indicating the file path where the output was saved.
        """
        # Abrir el archivo en modo de escritura
        filename = os.path.join('files', 'logs', 'output.log')
        with open(filename, 'a', encoding='utf-8') as file:
            # Imprimir y guardar la conversación
            file.write("\n\nConversación:\n")
            for phrase in self.result.get('phrases'):
                file.write(f"\t{phrase.speaker}: {phrase.text}\n")
            
            file.write(f"\nLista de errores:\n{self.errors_summary}")
            
            file.write("\nPuntuaciones:\n")
            try:
                # Imprimir y guardar las puntuaciones
                for category, data in self.result['score'].items():
                    file.write(f"\t{category.capitalize()}: Puntuación = {data.get('score')}, Explicación = {data.get('explanations')}\n")
            except Exception:
                # Si el modelo no ha devuelto las puntuaciones en formato JSON
                file.write(self.result)

        logger.info(f"Output saved to {filename}")

    def followPhraseology(self):
        """
        This function iterates through the phrases stored in `self.result['phrases']`, retrieves the text of each phrase,
        and returns a boolean value for each phrase indicating whether or not the phrase follows the phraseology.

        Returns:
            list[tuple]: A list of tuples, where each tuple contains:
                - str: The text of the phrase.
                - bool: `False` indicates the phrase does not follow the required phraseology, and `True` indicates it does.
        """
        phrases = []

        for phrase in self.result['phrases']:
            phrases.append((phrase.text, not phrase.otherPhraseology))

        return phrases
