# VLAS v2.0 - Estrategia de Desarrollo e Implementación

## 1. Visión del Producto
Desarrollar una solución comercialmente viable para el análisis automático de comunicaciones ATC (Air Traffic Control). El sistema debe ser capaz de transcribir, diarizar (identificar hablantes) y validar el cumplimiento normativo (SERA y RCA) con alta precisión.

## 2. Decisiones Tecnológicas

### 2.1 Motor de Transcripción
*   **Modelo Principal:** `faster-whisper` (implementación optimizada con CTranslate2).
*   **Versión:** `large-v3` (o variante fine-tuned para ATC como `whisper-large-v3-atco2-asr`).
*   **Justificación:** Ofrece el mejor equilibrio entre velocidad de inferencia (hasta 4x más rápido que Whisper original) y precisión en terminología aeronáutica.

### 2.2 Motor de Validación (El Inspector)
*   **Arquitectura:** **LangGraph** para orquestar flujos de razonamiento complejos.
*   **Modelos LLM:**
    *   **Cloud:** Google Gemini 1.5 Pro (por su ventana de contexto masiva y capacidad multimodal).
    *   **Local (Fallback):** Modelos Ollama (Phi-4 o Llama 3) para despliegues on-premise.
*   **Reglas:** Base de conocimiento vectorial (RAG) construida sobre los documentos en `/sources` (SERA y RCA).

## 3. Hoja de Ruta Inmediata

1.  **Consolidación del Core:**
    *   Asegurar que `api/transcriber.py` usa `faster-whisper` de forma estable.
    *   Optimizar la tubería de limpieza de audio.
2.  **Integración de Conocimiento:**
    *   Procesar los PDFs de `sources` para que el validador tenga La Ley exacta a mano.
3.  **Refinamiento de Agentes:**
    *   Mejorar el `Validator` (actualmente en `api/validator`) para que cite artículos específicos del reglamento en sus correcciones.
