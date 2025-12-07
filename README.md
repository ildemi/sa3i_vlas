# VLAS (vlas_m)
**VLAS** is a system that leverages AI-driven agents to handle transcription and validation of aviation communication conversations between Air Traffic Control Operators (ATCOs) and pilots. The project is designed to ensure compliance with aviation communication standards.

## Features  

### 1. **Transcription Module**  
- Utilizes **Whisper AI**, fine-tuned for ATCO communications.  
- Converts aviation communication audio into standardized text.  
- Employs **AI agents** to evaluate and select the best transcription from multiple outputs, ensuring the most accurate and contextually appropriate result.  
- Handles technical terms, translating them into a consistent format for further processing. 

### 2. **Validation Module**  
- Implements an intelligent validation system using **LangGraph** and **Large Language Models (LLMs)**.  
- Verifies communication adherence to aviation standards by analyzing:  
  - Standard phraseology usage.  
  - Call signs.  
  - Collation (read-back).  
  - Consistent language use.  
- Logs identified errors and provides explanations for each issue.
