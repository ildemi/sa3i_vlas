# Nota Técnica: Estrategia de Adaptación de Dominio (Fine-Tuning) para ATC Híbrido

**Proyecto:** VLAS (Voice Legal Analysis System)  
**Fecha:** 8 de Diciembre de 2025  
**Autor:** Antigravity (Assistant) & VLAS Architect

---

## 1. El Desafío: ATC Híbrido y "Code-Switching"

### Contexto Operativo
El modelo actual (`whisper-large-v3-atco2-asr`) es el estado del arte para comunicaciones ATC internacionales, habiendo sido entrenado con miles de horas de audio del espacio aéreo europeo y norteamericano. Sin embargo, su entrenamiento tiene un sesgo fundamental: **está optimizado para el Inglés como "Lingua Franca".**

En la realidad operativa de los aeródromos y centros de control en España (y otros países no angloparlantes), la comunicación es **híbrida**:
1.  **Comercial / Internacional:** Inglés estándar ICAO.
2.  **Doméstico / VFR:** Español.
3.  **Tierra / Colaterales:** Personal de handling, señaleros, OPS y coordinaciones telefónicas suelen ocurrir exclusivamente en Español.

### El Problema Técnico
Un modelo entrenado solo en inglés (o con poco español) tiende a sufrir alucinaciones cuando escucha español rápido con ruido de fondo, intentando forzar palabras inglesas donde no las hay (ej: interpretar "Autorizado a cruzar" como "Authorized to cross" o fonéticamente similar).

---

## 2. La Solución: Ajuste Fino (Fine-Tuning)

No necesitamos crear un modelo desde cero (lo cual costaría millones de euros en computación). Necesitamos especializar un modelo que ya es listo. A esto se le llama **Fine-Tuning**.

### Analogía Educativa
*   **Modelo Base (OpenAI Whisper):** Un estudiante universitario brillante que sabe muchos idiomas pero no sabe de aviones.
*   **Modelo Actual (ATCO2):** Ese estudiante tras un máster en ATC en Londres. Sabe muchísima fraseología, pero piensa en inglés.
*   **Modelo Objetivo (VLAS-ES):** Coger al graduado ATCO2 y enviarlo de prácticas 6 meses a la Torre de Barajas. Aprenderá la mezcla real de idiomas.

---

## 3. Metodología Técnica: PEFT y LoRA

Entrenar un modelo de 1.500 millones de parámetros (Whisper Large) tradicionalmente requiere clústeres de GPUs industriales. Sin embargo, podemos hacerlo en local (con tu **RTX 2080 Ti**) usando técnicas modernas.

### LoRA (Low-Rank Adaptation)
En lugar de re-entrenar todo el cerebro de la red neuronal, **congelamos** el modelo original y añadimos pequeñas capas adicionales ("adaptadores") que son las únicas que se modifican.
*   **Eficiencia:** Reduce el uso de memoria VRAM en un 70%.
*   **Portabilidad:** El resultado no es un modelo nuevo de 3GB, sino un archivo pequeño (~100MB) que se carga "encima" del original.

---

## 4. El Ciclo Virtuoso VLAS (Data Engine)

La parte más difícil no es el código de entrenamiento, sino los **DATOS**. Para entrenar, necesitamos "Ground Truth" (La Verdad Absoluta): audios emparejados con su transcripción perfecta.

VLAS v2.0 se convierte en la herramienta perfecta para generar este dataset:

1.  **Fase de Uso (Inferencia):**
    *   Sube audios y obtén una transcripción "borrador" (automática).
2.  **Fase de Corrección (Human-in-the-loop):**
    *   Un controlador humano revisa el texto en VLAS.
    *   Corrige "Iberia tree four" por "Iberia 34".
    *   Corrige "Rodar vía bravo" donde la IA puso "Runway via bravo".
3.  **Fase de Almacenamiento:**
    *   VLAS guarda esa corrección en la base de datos como **Dato de Entrenamiento Válido**.
4.  **Fase de Entrenamiento (Batch):**
    *   Cuando reunimos ~10-50 horas de audios corregidos, ejecutamos el script de entrenamiento nocturno.

---

## 5. Prevención de Riesgos: Olvido Catastrófico

Si entrenamos al modelo solo con audios en español de tierra, el modelo puede sufrir "Catastrophic Forgetting" y empezar a transcribir mal el inglés.

**Estrategia de Mitigación:**
El Dataset de entrenamiento debe ser **MIXTO**:
*   **50%** Nuevos audios híbridos (Español/Inglés de tus torres).
*   **50%** Audios originales en Inglés puro (del dataset ATCO2 o LibriSpeech).

Esto fuerza al modelo a mantener su competencia en inglés mientras adquiere la nueva habilidad en español, aprendiendo a hacer **Code-Switching** (cambiar de idioma fluidamente según el contexto).

---

## 6. Roadmap de Implementación

1.  **Habilitar Edición en VLAS:** Asegurar que el frontend permite corregir y guardar transcripciones.
2.  **Exportador de Dataset:** Crear un script que extraiga `(audio, texto_corregido)` de la DB en formato HuggingFace.
3.  **Script de Entrenamiento:** Implementar un pipeline de entrenamiento usando librerías `transformers`, `peft` y `bitsandbytes`.
4.  **Evaluación:** Comparar el WER (Word Error Rate) del modelo nuevo vs. el antiguo usando un set de audios de prueba que el modelo nunca haya visto antes.
