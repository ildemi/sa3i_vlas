# Estrategia de Normalización y Corrección de Transcripciones (VLAS v2.0)

## 0. Introducción y Contexto
Los modelos ASR de propósito general (incluso los fine-tuned como `whisper-large-v3-atco2`) sufren de "pérdida de contexto" en entornos mixtos idioma/jerga técnica. En concreto, el modelo tiende a:
1.  Transcribir letras ICAO como letras simples (*"A"* en vez de *"Alfa"*).
2.  Confundir términos ICAO con nombres comunes en español (*"Victoria"* por *"Victor"*, *"Zeta"* por *"Zulu"*).
3.  Perder la estructura de códigos de pista o rumbos.

Para solucionar esto sin re-entrenar (caro y lento), se establece una estrategia en capas.

## Estrategia Combinada (Layered Approach)

### Capa 1: Whisper Initial Prompt (Context Priming)
Se condiciona al modelo **antes** de que genere el primer token.
*   **Mecanismo:** Pasar una cadena de texto al parámetro `initial_prompt` de Whisper.
*   **Contenido:** Una frase que contenga todo el alfabeto ICAO y términos clave.
*   **Ejemplo:** *"Comunicaciones ATC en español. Alfabeto: Alfa, Bravo, Charlie, Delta, Echo, Foxtrot, Golf, Hotel, India, Juliett, Kilo, Lima, Mike, November, Oscar, Papa, Quebec, Romeo, Sierra, Tango, Uniform, Victor, Whiskey, X-ray, Yankee, Zulu. Términos: Rodadura, Pista, Viento, QNH, Autorizado."*

### Capa 2: Normalización Determinista (Post-Processing Regex)
Se aplica **inmediatamente después** de recibir el texto de Whisper, antes de guardar en BD. Es rápida y corrige errores sistemáticos.

**Reglas de Diccionario (Borrador Inicial):**

| Patrón Detectado (Input) | Contexto (Regex) | Sustitución (Output) | Razón |
| :--- | :--- | :--- | :--- |
| **Letras Aisladas** | | | |
| `\b(A\|a)\b` | Letra 'a' sola entre espacios | `Alfa` | Evita "Autoriza a la pista" -> "Alfa la pista"? **CUIDADO**: Requiere contexto de matrícula. |
| `\b(b\|B)\b` | Letra 'b' sola | `Bravo` | |
| `pista\s+(\d{2})` | Palabra 'pista' seguida de 2 dígitos | `pista \1` | Normalización de pistas (ej: 04, 22) |
| **Nombres Confusos** | | | |
| `\bVictoria\b` | Palabra exacta | `Victor` | Error muy común en español. |
| `\bZeta\b` | Palabra exacta | `Zulu` | Confusión fonética Z/Zulu. |
| `\bCoca\b` | Palabra exacta | `Coca` (NO CAMBIAR) | A veces usado informalmente por 'Charlie' en España, ¿normalizamos a Charlie? **A definir**. |
| `\bIndia\b` | | `India` | Correcto. |
| `\bIndio\b` | Palabra exacta | `India` | Error común. |
| `\bJulieta\b` | Palabra exacta | `Juliett` | Españolización de Juliett. |

**Nota sobre la Letra 'A':**
Sustituir todas las 'A' por 'Alfa' es peligroso en español ("Voy **a** la plataforma").
*   *Regla Refinada:* Solo sustituir si está cerca de números o en formato matrícula (ej: "EC-M**A**"). Esta capa quizás deba ser conservadora y dejar las letras dudosas para la Capa 3.

### Capa 3: Corrección Semántica con LLM (Ollama)
Se aplica cuando la heurística (Capa 2) no es suficiente.
*   **Modelo:** Phi-4, Llama3 o Gemma (modelos ligeros).
*   **Prompt de Sistema:**
    > "Eres un corrector de transcripciones ATC. Tu ÚNICO trabajo es corregir errores tipográficos del alfabeto ICAO y formato de números.
    > Input: 'Rodaje a punto de espera alfa de la pista dos cuatro.'
    > Output: 'Rodaje a punto de espera **Alfa** de la pista **24**.'
    > NO cambies palabras que no sean códigos técnicos. NO resumas."

## Plan de Implementación Técnica

1.  **Fase 1:** Implementar **Capa 2** (Módulo `api/transcriber/normalize_rules.py`).
2.  **Fase 2:** Implementar **Capa 1** (Añadir `initial_prompt` en `transcriber.py`).
3.  **Fase 3:** Evaluar resultados. Si persisten errores graves, activar **Capa 3**.
