# Nota Técnica: Arquitectura y Conceptos de VLAS v2.1

**Fecha:** 8 de Diciembre de 2025  
**Proyecto:** VLAS (Voice Legal Analysis System)  
**Versión:** 2.2 (Actualizada con Estrategias de Normalización)

## 1. Visión General de la Arquitectura (Microservicios)

VLAS v2.0 abandona la arquitectura monolítica antigua para adoptar un diseño basado en **microservicios** orquestados con Docker. Esto significa que la aplicación no es un único bloque, sino un conjunto de "departamentos" especializados que colaboran entre sí.

### Componentes Principales

| Componente | Tecnología | Rol (Analogía) | Función Técnica |
| :--- | :--- | :--- | :--- |
| **Frontend** | React + Vite | **El Escaparate** | Interfaz de usuario. Envía audios y muestra resultados. |
| **Backend** | Django (Python) | **El Gerente** | Recibe peticiones, gestiona usuarios y seguridad. Delega el trabajo pesado. |
| **Base de Datos** | PostgreSQL | **La Memoria** | Almacena usuarios, metadatos de audios y tablas de normalización. |
| **Broker** | RabbitMQ | **La Comanda** | Cola de mensajería. Gestiona la lista de tareas pendientes. |
| **Worker** | Celery | **El Cocinero** | Procesa las tareas pesadas (IA) en segundo plano para no bloquear la web. |

---

## 2. El Motor de Transcripción (El Oído)

Esta es la pieza crítica donde convertimos audio en texto. Aquí es donde surgen las diferencias entre formatos y motores.

### Diferencia: Modelo vs. Motor
*   **El Modelo (El Piloto):** Es el "conocimiento". En nuestro caso, `whisper-large-v3-atco2-asr`. Sabe reconocer palabras aeronáuticas.
*   **El Motor (El Coche):** Es el software que ejecuta ese modelo. Usamos `faster-whisper`.

### ¿Por qué `faster-whisper`?
Usamos `faster-whisper` en lugar del `whisper` original de OpenAI por una razón: **CTranslate2**.

#### ¿Qué es CTranslate2 (CT2)?
*   **Origen:** Desarrollado por **OpenNMT** (Harvard/SYSTRAN) originalmente para traducción de texto.
*   **Propósito:** Es un motor de inferencia escrito en C++ diseñado para ejecutar modelos de arquitectura Transformer (como Whisper) con **máxima eficiencia**.
*   **Ventaja:** Permite técnicas como la **cuantización** (reducir la precisión de números de 32 bits a 16 o 8 bits sin perder apenas calidad), lo que hace que el modelo corra **hasta 4 veces más rápido** y ocupe menos memoria RAM/VRAM.

### El Conflicto de Formatos: PyTorch vs. CT2
*   **HuggingFace / PyTorch:** Es la "biblioteca" estándar donde se publican los modelos. Los archivos suelen ser `.bin` o `.pt` diseñados para ser leídos por la librería `transformers` de Python.
*   **El Problema:** `faster-whisper` no entiende "nativo" PyTorch. Necesita que los "pesos" del modelo estén organizados en su propio formato binario optimizado.
*   **La Solución:** El modelo debe ser **convertido** (traducido) del formato PyTorch al formato CT2. Esto lo puede hacer la librería automáticamente al descargar si se configura correctamente.

---

## 3. El Motor de Validación (El Cerebro)

Una vez tenemos el texto, necesitamos entenderlo y juzgarlo legalmente.

### Ollama & LLMs
*   **Tecnología:** Ollama es un runtime ligero para ejecutar **LLMs** (Large Language Models) localmente.
*   **Modelo:** Usamos **Phi-4** (de Microsoft), un modelo pequeño pero muy potente en razonamiento lógico.
*   **¿Por qué no usar Ollama para Whisper?** Ollama está optimizado para modelos generativos de texto (tipo Chat/GPT), prediciendo la siguiente palabra. Whisper es un modelo "Audio-to-Text" con una arquitectura diferente (Encoder-Decoder), por lo que requiere su propio motor especializado (`faster-whisper`).

---

## 4. Estrategia de Normalización y Limpieza (VLAS v2.2)

Dada la naturaleza crítica de las comunicaciones ATC y el sesgo de los modelos ASR hacia el inglés, hemos implementado una estrategia de corrección en capas ("Layered Approach") para garantizar la máxima fidelidad técnica.

### Capa 1: Context Priming (Pre-Inferencia)
Se condiciona al modelo Whisper mediante el parámetro `initial_prompt`.
*   **Objetivo:** Reducir la probabilidad de que el modelo transcriba fonemas ambiguos como palabras comunes.
*   **Implementación:** Inyección de una cadena con el alfabeto ICAO completo y términos clave al inicio de cada tarea de transcripción.

### Capa 2: Normalización Determinista (Post-Inferencia)
Módulo de *sanitización* inmediata basado en reglas rígidas (Regex/Diccionarios).
*   **Objetivo:** Corregir errores sistemáticos conocidos (ej: "Victoria" -> "Victor", "uno" -> "1").
*   **Herramienta:** Módulo `api/transcriber/normalization_rules.py`.
*   **Reglas:** Diccionario estático mantenido por expertos ATC.

### Capa 3: Corrección Semántica (LLM) - *Planificada*
Validación final de coherencia mediante IA Generativa (Ollama/Phi-4).
*   **Objetivo:** Resolver ambigüedades dependientes del contexto (ej: distinguir si "pista" se refiere a la RWY o a una instrucción).

## 5. Flujo de Datos Actualizado

1.  **Ingesta:** Usuario sube `audio.wav`.
2.  **Procesamiento (Celery):**
    *   **Diarización:** Segmentación por hablantes (`pyannote`).
    *   **Transcripción Mejorada:** Whisper (Beam=15) + `initial_prompt`.
    *   **Normalización:** Aplicación de diccionario (Capa 2: `normalization_rules.py`).
3.  **Identificación de Rol (Futuro):** Clasificación del hablante (ATCO/Piloto) basada en sintaxis.
4.  **Almacenamiento:** Guardado en PostgreSQL.

---

## 6. Profundización Técnica: El Motor de Transcripción (Deep Dive)

A petición del usuario, detallamos la mecánica interna de la interacción Motor-Modelo y las estrategias de decodificación.

### 5.1. La Relación Motor vs. Modelo (El Músico y la Partitura)
Para entender qué ocurre dentro de VLAS, usamos la analogía de la música:

| Concepto | Componente Técnico | Analogía | Función |
| :--- | :--- | :--- | :--- |
| **El Modelo** | `whisper-large-v3-atco2` | **La Partitura** | Contiene el conocimiento estático (matemáticas congeladas). Define **QUÉ** sabe el sistema. Es un archivo pasivo (`model.bin`) creado por el entrenamiento (OpenAI/ATCO2). |
| **El Motor** | `faster-whisper` (CT2) | **El Pianista** | Es el ejecutor. Sabe leer la partitura y tocarla. Gestiona los recursos (dedos/GPU), la velocidad y la memoria. Define **CÓMO** se ejecuta. |

#### Flujo de Interacción:
1.  **Ingesta:** El Motor (Faster-Whisper) recibe el audio (mp3/wav) y lo decodifica a una onda cruda a 16kHz usando FFMPEG.
2.  **VAD (Voice Activity Detection):** El Motor recorta los silencios para no perder tiempo analizando "nada".
3.  **Encodificación:** El Motor pasa trozos de 30 segundos de audio a la GPU para que el Modelo los convierta en una matriz matemática (representación latente).
4.  **Decodificación (Beam Search):** El Motor explora esa matriz para encontrar las palabras más probables.

---

### 5.2. El Proceso de Decodificación (Beam Search)

Una vez que el Modelo ha generado las probabilidades matemáticas para el siguiente sonido, el Motor debe decidir qué palabra escribir. Aquí entra el algoritmo de búsqueda.

*   **Greedy Search (Beam = 1):** El motor elige siempre la opción con mayor probabilidad inmediata. Es rápido pero miope. Si se equivoca en una letra, puede arrastrar el error toda la frase.
*   **Beam Search (Búsqueda en Haz):** El motor mantiene vivas varias hipótesis "en paralelo".
    *   **Ejemplo (Beam = 5):** *"El sonido parece 'Hola' (60%) o 'Ola' (40%). Me guardo las dos. Si la siguiente palabra es 'mar', entonces 'Ola de mar' (40% * 80%) gana a 'Hola de mar' (60% * 1%)."*

**¿Qué pasa si subimos a `beam_size=20`?**
*   **Ventaja:** El sistema explora un árbol de posibilidades mucho más amplio. Es capaz de corregir errores fonéticos basándose en el contexto gramatical lejano.
*   **Desventaja:** El coste computacional crece linealmente. `Beam 20` es aproximadamente 4 veces más lento que `Beam 5`.
*   **Punto Dulce:** En ATC, donde el contexto es vital ("Two" vs "To"), un Beam de **10** (ahora subido a **15** en VLAS v2.2) suele ser el equilibrio perfecto entre precisión y velocidad.

---

### 5.3. Ventaja Competitiva: CTranslate2 vs. PyTorch Original

¿Por qué nos esforzamos tanto en usar `faster-whisper` (CTranslate2) en lugar del estándar de HuggingFace (PyTorch)?

1.  **Velocidad Pura:** CTranslate2 es un motor C++ dedicado. Elimina toda la sobrecarga (overhead) de Python y PyTorch. Es **4x más rápido**.
2.  **Gestión de Memoria (VRAM):**
    *   **PyTorch:** Carga el modelo completo en 32 bits. `Whisper Large` ocupa ~6GB de VRAM.
    *   **CTranslate2:** Permite **Cuantización Inteligente** (`float16` o `int8`).
        *   `float16` (tu configuración actual): Ocupa ~3GB, mantiene 99.9% precisión.
        *   `int8`: Ocupa ~1.5GB, mantiene 98% precisión, vuela en CPUs.
3.  **Ejecución "Non-Blocking":** Permite liberar el GIL (Global Interpreter Lock) de Python, lo que facilita que Celery haga otras cosas mientras la GPU trabaja.

**Veredicto:** En un entorno de producción como VLAS v2.1, usar la implementación original de PyTorch sería un desperdicio de recursos y tiempo. La arquitectura actual (CT2 + GPU NVIDIA) es el estado del arte en eficiencia.
