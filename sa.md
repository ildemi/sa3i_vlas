# Situational Awareness (SA) - VLAS v2.2 Project

## 1. Project Overview
**VLAS (Voice Legal Analysis System)** is a commercial-grade application designed for **Hybrid ATC Environments** (Spanish/English).
**Core Mission:**
1.  **Transcribe** mixed ATC communications using specialized models (`faster-whisper` + `large-v3-atco2`).
2.  **Normalize** output using a multi-layer strategy (Context Priming -> Deterministic Regex -> LLM Semantic Correction).
3.  **Analyze** adherence to SERA/RCA regulations using LLMs.
4.  **Train** custom models (Fine-tuning) via a "Human-in-the-loop" data engine.

## 2. System Architecture
*   **Root Path:** `c:\Users\esdei\sa3i_vlas`
*   **Backend (`/api`):** Python/Django + Celery + RabbitMQ.
    *   **ASR Engine:** `faster-whisper` (CTranslate2 backend, `float16` quantization) for 4x speed.
    *   **Logic:** `transcriber` (Audio processing), `validator` (LLM analysis).
    *   **Normalization:** Database-backed deterministic rules + Whisper Prompting.
*   **Frontend (`/web`):** React + Vite + TypeScript.
*   **AI/LLM:**
    *   **Transcription:** `whisper-large-v3-atco2-asr`.
    *   **Validation:** Local Ollama (Phi-4) or Cloud Gemini 1.5 Pro.
*   **Infrastructure:** Dockerized Microservices (`vm_vlas` network).

## 3. Current Status (2025-12-09)
**Phase:** Normalization Engine COMPLETE.

### Recent Victories
1.  **Project Structure:** Cleaned up `api` vs `models` app conflict. Now `api` is the single source of truth.
2.  **Normalization Seeding:** Successfully moved legacy regex rules + NATO alphabet into PostgreSQL.
3.  **Layer 2 Implementation:** Refactored `normalize.py` to load rules dynamically from DB.
4.  **Verification:** Validated that "uno" -> "1" works via Django Shell.

### Critical Blockers
*   None.

### Next Steps
1.  **Add Missing Rules:** Some legacy dictionaries were incomplete (e.g. "Victoria" -> "Victor" was missing). We need a way to add rules easily (Admin Panel?).
2.  **Layer 1 (Prompting):** Verify `initial_prompt` in `transcriber.py`.
3.  **Frontend Integration:** Ensure frontend displays the corrected text.

## 4. IMMEDIATE ACTION PLAN
**Done.** The Normalization Engine is active.
Any new transcription will query the DB for rules.

To add new rules:
Use Django Admin (`/admin`) to add `TranscriptionCorrection` entries.


If Docker/Ports fail or session resets:
1.  **Start Docker Desktop** & wait for green light.
2.  `cd c:\Users\esdei\sa3i_vlas`
3.  `docker compose -f docker/docker-compose.yml --env-file .env up -d`
4.  **Check migrations:** `docker exec vlas-django-1 python manage.py migrate`
5.  **Green Status:** Check `http://localhost:8080` -> IA Status.
