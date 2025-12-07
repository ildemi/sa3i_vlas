<template>
  <div class="container">
    <div class="card shadow-sm">
      <div class="card-body">
        <router-link to="/history" class="btn btn-outline-primary mb-3">Back to History</router-link>

        <h2 class="card-title text-center mb-4">Validation Results</h2>

        <!-- Loading Screen -->
        <div v-if="isLoading" class="text-center my-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2">Loading validation results...</p>
        </div>

        <!-- Error Message -->
        <div v-else-if="error" class="alert alert-danger text-center">
          {{ error }}
        </div>

        <!-- Validation Results -->
        <div v-else class="validation-results">
          <!-- Validation calification form -->
          <div class="validation-calification-form mb-4">
            <h3>Validation Calification</h3>
            <p class="text-muted">Please provide your feedback and score for the validation.</p>
            <form @submit.prevent="submitCalification">
              <div class="mb-3">
                <label for="calification" class="form-label">Calification (0-5):</label>
                <input
                  type="number"
                  v-model="validationData.validation_calification"
                  min="0"
                  max="5"
                  step="0.1"
                  class="form-control w-auto"
                  id="calification"
                  required
                >
              </div>

              <div class="mb-3">
                <label for="comment" class="form-label">Comment:</label>
                <textarea
                  v-model="validationData.validation_comment"
                  class="form-control"
                  id="comment"
                  rows="3"
                  placeholder="Write your feedback here..."
                  required
                ></textarea>
              </div>

              <button type="submit" class="btn btn-primary">Submit</button>
            </form>
          </div>

          <div class="group-info mb-4">
            <h3>{{ groupName }}</h3>
            <div class="validation-meta d-flex justify-content-between align-items-center mb-3">
              <span class="validation-date">
                Validated on: {{ formatDate(validationData.validation_date) }}
              </span>
              <div class="score-badge" v-if="validationData.validation_score !== null">
                <span class="score-label">Score:</span>
                <span class="score-value" :class="scoreClass">
                  {{ formatScore(validationData.validation_score) }}
                </span>
                <div class="score-progress-container">
                  <div class="score-progress-bar" :class="scoreClass" :style="{ width: calculatePercentage(validationData.validation_score) + '%' }"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Error Summary -->
          <div class="error-summary card mb-4" v-if="hasLanguageErrors || hasCollationErrors || hasCallSignErrors">
            <div class="card-header bg-warning text-dark">
              <h4 class="mb-0">Error Summary</h4>
            </div>
            <div class="card-body">
              <div v-if="hasLanguageErrors" class="language-error mb-3">
                <h5>Language Errors:</h5>
                <div class="alert alert-warning">
                  {{ validationData.validation_result.language_error }}
                </div>
              </div>

              <div v-if="hasCollationErrors" class="collation-error">
                <h5>Collation Errors:</h5>
                <div class="alert alert-warning">
                  {{ validationData.validation_result.collation_error.explanation }}
                </div>
              </div>

              <!-- Callsign Errors -->
              <div v-if="hasCallSignErrors" class="callsign-error">
                <h5>Callsign Errors:</h5>
                <div class="alert alert-warning">
                  {{ validationData.validation_result.callsign_error }}
                </div>
              </div>
            </div>
          </div>

          <!-- Detailed Scores -->
          <div class="scores-detail card mb-4" v-if="hasScores">
            <div class="card-header bg-info text-white d-flex justify-content-between align-items-center">
              <h4 class="mb-0">Detailed Scores</h4>
              <button class="btn btn-sm btn-light" @click="downloadScoreReport" title="Download score report">
                <i class="bi bi-download"></i> Download
              </button>
            </div>
            <div class="card-body">
              <div class="overall-score-container mb-4" v-if="validationData.validation_score !== null">
                <h5 class="category-title">Overall Score</h5>
                <div class="overall-score p-3 border rounded">
                  <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="score-name">Overall Evaluation:</span>
                    <span class="score-number" :class="scoreClass">{{ formatScore(validationData.validation_score) }}</span>
                  </div>
                  <div class="score-progress-container mb-3">
                    <div class="score-progress-bar" :class="scoreClass" :style="{ width: calculatePercentage(validationData.validation_score) + '%' }"></div>
                  </div>
                  <div class="overall-feedback" v-if="getOverallFeedback()">
                    <p>{{ getOverallFeedback() }}</p>
                  </div>
                </div>
              </div>

              <div v-for="(scoreObj, index) in scoreItems" :key="index" class="score-category mb-3">
                <h5 class="category-title">{{ formatCategory(scoreObj.category) }}</h5>
                <div class="score-details p-3 border rounded">
                  <div v-if="typeof scoreObj.value === 'object' && scoreObj.value !== null" class="score-item">
                    <div v-if="scoreObj.value.score !== undefined" class="d-flex justify-content-between align-items-center mb-2">
                      <span class="score-name">Score:</span>
                      <span class="score-number">{{ formatScore(scoreObj.value.score) }}</span>
                    </div>
                    <div v-if="scoreObj.value.score !== undefined" class="score-progress-container mb-2">
                      <div class="score-progress-bar" :class="getScoreClass(scoreObj.value.score)" :style="{ width: calculatePercentage(scoreObj.value.score) + '%' }"></div>
                    </div>
                    <div v-if="scoreObj.value.explanation" class="score-explanation">
                      <p>{{ scoreObj.value.explanation }}</p>
                    </div>
                    <!-- Show specific details if they exist -->
                    <div v-if="scoreObj.value.details" class="score-details-list mt-3">
                      <h6>Details:</h6>
                      <ul class="list-group">
                        <li v-for="(detail, dIndex) in scoreObj.value.details" :key="dIndex" class="list-group-item">
                          {{ detail }}
                        </li>
                      </ul>
                    </div>
                  </div>
                  <div v-else class="score-item">
                    <p>{{ scoreObj.value }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Phrase Analysis -->
          <div class="phrases-analysis card mb-4" v-if="hasPhrases">
            <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
              <h4 class="mb-0">Phrase Analysis</h4>
              <button class="btn btn-sm btn-light" @click="downloadPhraseAnalysis" title="Download phrase analysis">
                <i class="bi bi-download"></i> Download
              </button>
            </div>
            <div class="card-body">
              <div v-for="(phrase, index) in validationData.validation_result.phrases" :key="index" class="phrase-item p-3 mb-3 border rounded">
                <div class="d-flex justify-content-between mb-2">
                  <span class="speaker-badge" :class="{'badge-pilot': phrase.speaker === 'pilot', 'badge-atco': phrase.speaker === 'atco'}">
                    {{ phrase.speaker.toUpperCase() }}
                  </span>
                  <span class="status-badge" :class="getPhraseStatusClass(phrase)">
                    {{ getPhraseStatus(phrase) }}
                  </span>
                </div>
                <div class="phrase-text mb-2">
                  <p class="original-text mb-1">{{ phrase.text }}</p>
                </div>
                <div v-if="phrase.matched_rule || phrase.rule" class="phrase-rule mt-2 p-2 border-top">
                  <div class="rule-title mb-1">Identified Rule:</div>
                  <div class="rule-text">{{ phrase.matched_rule || phrase.rule }}</div>
                </div>
                <div v-if="phrase.phraseology_error || phrase.phraseologyFails" class="phrase-error mt-2 p-2 border-top">
                  <div class="error-title mb-1 text-danger">Phraseology Error:</div>
                  <div class="error-text">{{ phrase.phraseology_error || phrase.phraseologyFails }}</div>
                </div>
                <!-- Additional information about keywords -->
                <div v-if="phrase.keywords && phrase.keywords.length > 0" class="phrase-keywords mt-2 p-2 border-top">
                  <div class="keywords-title mb-1">Identified Keywords:</div>
                  <div class="keywords-list">
                    <span v-for="(keyword, kIndex) in phrase.keywords" :key="kIndex" class="keyword-badge">
                      {{ keyword }}
                    </span>
                  </div>
                </div>
                <!-- Callsign Error -->
                <div v-if="phrase.callSignFailure && phrase.callSignFailure !== 'Correct'" class="callsign-error mt-2 p-2 border-top">
                  <div class="error-title mb-1 text-danger">Callsign Error:</div>
                  <div class="error-text">{{ phrase.callSignFailure }}</div>
                </div>
                <!-- Supervision information if it exists -->
                <div v-if="phrase.supervised && (phrase.supervised.explanation || phrase.supervised.counter > 0)" class="supervision-info mt-2 p-2 border-top">
                  <div class="supervision-title mb-1">Supervision:</div>
                  <div class="supervision-details">
                    <p v-if="phrase.supervised.counter > 0" class="mb-1">Reviewed {{ phrase.supervised.counter }} times</p>
                    <p v-if="phrase.supervised.explanation">{{ phrase.supervised.explanation }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { useToast } from 'vue-toastification'

interface ScoreItem {
  category: string;
  value: any;
}

const route = useRoute()
const toast = useToast()

const isLoading = ref(true)
const error = ref('')
const validationData = ref<any>({})
const groupName = ref('')

onMounted(async () => {
  await fetchValidationResults()
})

async function fetchValidationResults() {
  try {
    isLoading.value = true
    error.value = ''

    const groupId = route.params.groupId as string
    if (!groupId) {
      error.value = 'ID de grupo no encontrado'
      return
    }

    const djangourl = import.meta.env.VITE_DJANGO_URL

    // Primero obtenemos la información básica del grupo
    const groupResponse = await axios.get(`${djangourl}transcription-group/${groupId}/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })

    groupName.value = groupResponse.data.group_name

    // Luego obtenemos los resultados de la validación
    const validationResponse = await axios.get(`${djangourl}group-validation-results/${groupId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })

    validationData.value = validationResponse.data
  } catch (error: any) {
    console.error('Error al cargar los resultados de validación:', error)

    if (error.response && error.response.status === 404) {
      error.value = 'Este grupo no tiene resultados de validación'
    } else {
      error.value = 'Error al cargar los resultados de validación'
      toast.error('Error al cargar los resultados de validación')
    }
  } finally {
    isLoading.value = false
  }
}

const hasLanguageErrors = computed(() => {
  return validationData.value?.validation_result?.language_error &&
         validationData.value.validation_result.language_error !== ''
})

const hasCollationErrors = computed(() => {
  return validationData.value?.validation_result?.collation_error?.explanation &&
         validationData.value.validation_result.collation_error.explanation !== ''
})

const hasCallSignErrors = computed(() => {
  return validationData.value?.validation_result?.callsign_error &&
         validationData.value.validation_result.callsign_error !== ''
})

const hasScores = computed(() => {
  return validationData.value?.validation_result?.score &&
         Object.keys(validationData.value.validation_result.score).length > 0
})

const hasPhrases = computed(() => {
  return validationData.value?.validation_result?.phrases &&
         validationData.value.validation_result.phrases.length > 0
})

const scoreItems = computed(() => {
  if (!validationData.value?.validation_result?.score) return []

  return Object.entries(validationData.value.validation_result.score).map(([category, value]) => {
    return { category, value } as ScoreItem
  })
})

const scoreClass = computed(() => {
  const score = validationData.value?.validation_score
  if (score === null || score === undefined) return ''

  if (score >= 4) return 'score-high'
  if (score >= 3) return 'score-medium'
  return 'score-low'
})

function submitCalification() {
  const djangourl = import.meta.env.VITE_DJANGO_URL;
  const groupId = route.params.groupId as string;

  axios.post(`${djangourl}transcription-group/${groupId}/calification/`, {
    validation_calification: validationData.value.validation_calification,
    validation_comment: validationData.value.validation_comment
  }, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  })
  .then(() => {
    toast.success('Calificación guardada con éxito');
  })
  .catch((error) => {
    console.error('Error al guardar la calificación:', error);
    toast.error('Error al guardar la calificación');
  });
}

function calculatePercentage(score: number | null | undefined): number {
  if (score === undefined || score === null) return 0
  return (score / 5) * 100
}

function getScoreClass(score: number | null | undefined): string {
  if (score === null || score === undefined) return ''

  if (score >= 4) return 'score-high'
  if (score >= 3) return 'score-medium'
  return 'score-low'
}

function formatDate(dateString: string | undefined): string {
  if (!dateString) return 'No disponible'

  const options = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  } as Intl.DateTimeFormatOptions

  const date = new Date(dateString)
  return date.toLocaleDateString('es-ES', options)
}

function formatScore(score: number | null | undefined): string {
  if (score === undefined || score === null) return 'N/A'
  return `${score.toFixed(1)}/5`
}

function formatCategory(category: string): string {
  // Convertir camelCase o snake_case a palabras con espacios y capitalizar
  return category
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase())
}

function getPhraseStatus(phrase: any): string {
  if (phrase.phraseology_error) {
    return 'Error'
  }

  return 'Validado'
}

function getPhraseStatusClass(phrase: any): string {
  if (phrase.phraseology_error) {
    return 'status-error'
  }
  if (phrase.matched_rule) {
    return 'status-success'
  }
  return 'status-neutral'
}

function getOverallFeedback() {
  const score = validationData.value?.validation_score
  if (score === null || score === undefined) return null

  if (score >= 4.5) return 'Excelente comunicación aeronáutica. Cumple con los estándares más altos.'
  if (score >= 4) return 'Muy buena comunicación. Pocas áreas de mejora.'
  if (score >= 3) return 'Comunicación aceptable pero con algunas áreas importantes para mejorar.'
  if (score >= 2) return 'Comunicación con deficiencias significativas. Se requiere entrenamiento adicional.'
  return 'Comunicación con problemas graves. Se recomienda formación inmediata.'
}

function downloadScoreReport() {
  if (!validationData.value?.validation_result) return

  // Crear contenido del informe
  let content = "INFORME DE VALIDACIÓN\n\n"
  content += `Grupo: ${groupName.value}\n`
  content += `Fecha de validación: ${formatDate(validationData.value.validation_date)}\n`
  content += `Puntuación global: ${formatScore(validationData.value.validation_score)}\n\n`

  // Añadir puntuaciones detalladas
  content += "PUNTUACIONES DETALLADAS:\n"
  for (const item of scoreItems.value) {
    content += `\n${formatCategory(item.category)}:\n`
    if (typeof item.value === 'object' && item.value !== null) {
      if (item.value.score !== undefined) {
        content += `- Puntuación: ${formatScore(item.value.score)}\n`
      }
      if (item.value.explanation) {
        content += `- Explicación: ${item.value.explanation}\n`
      }
      if (item.value.details && Array.isArray(item.value.details)) {
        content += "- Detalles:\n"
        for (const detail of item.value.details) {
          content += `  * ${detail}\n`
        }
      }
    } else {
      content += `- ${item.value}\n`
    }
  }

  // Añadir errores si existen
  if (hasLanguageErrors.value || hasCollationErrors.value || hasCallSignErrors.value) {
    content += "\nERRORES DETECTADOS:\n"

    if (hasLanguageErrors.value) {
      content += `\nErrores de Lenguaje:\n${validationData.value.validation_result.language_error}\n`
    }

    if (hasCollationErrors.value) {
      content += `\nErrores de Colación:\n${validationData.value.validation_result.collation_error.explanation}\n`
    }

    if (hasCallSignErrors.value) {
      content += `\nErrores de Indicativo:\n${validationData.value.validation_result.callsign_error}\n`
    }
  }

  // Crear blob y descargar
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `validacion_${groupName.value.replace(/\s+/g, '_')}_${new Date().toISOString().slice(0, 10)}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function downloadPhraseAnalysis() {
  if (!validationData.value?.validation_result?.phrases) return

  // Crear contenido del informe
  let content = "ANÁLISIS DE FRASES\n\n"
  content += `Grupo: ${groupName.value}\n`
  content += `Fecha de validación: ${formatDate(validationData.value.validation_date)}\n`
  content += `Puntuación global: ${formatScore(validationData.value.validation_score)}\n\n`

  // Análisis de cada frase
  for (const phrase of validationData.value.validation_result.phrases) {
    content += `${phrase.speaker.toUpperCase()}: "${phrase.text}"\n`
    content += `Estado: ${getPhraseStatus(phrase)}\n`

    if (phrase.matched_rule || phrase.rule) {
      content += `Regla identificada: ${phrase.matched_rule || phrase.rule}\n`
    }

    if (phrase.phraseology_error || phrase.phraseologyFails) {
      content += `Error de fraseología: ${phrase.phraseology_error || phrase.phraseologyFails}\n`
    }

    if (phrase.callSignFailure && phrase.callSignFailure !== 'Correcto') {
      content += `Error de indicativo: ${phrase.callSignFailure}\n`
    }

    if (phrase.keywords && phrase.keywords.length > 0) {
      content += `Palabras clave: ${phrase.keywords.join(', ')}\n`
    }

    if (phrase.supervised && (phrase.supervised.explanation || phrase.supervised.counter > 0)) {
      if (phrase.supervised.counter > 0) {
        content += `Revisado ${phrase.supervised.counter} veces\n`
      }
      if (phrase.supervised.explanation) {
        content += `Explicación de supervisión: ${phrase.supervised.explanation}\n`
      }
    }

    content += '\n---\n\n'
  }

  // Crear blob y descargar
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `analisis_frases_${groupName.value.replace(/\s+/g, '_')}_${new Date().toISOString().slice(0, 10)}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.container {
  width: 95%;
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0;
}

.card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-body {
  padding: 2rem;
}

.card-title {
  font-size: 2.5rem;
  color: #2196f3;
  margin-bottom: 1.5rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  background: linear-gradient(45deg, #2196f3, #1976d2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.btn-outline-primary {
  padding: 8px 18px;
  border-radius: 30px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.validation-meta {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
}

.validation-date {
  color: #6c757d;
  font-style: italic;
}

.score-badge {
  background: #e9ecef;
  padding: 8px 15px;
  border-radius: 30px;
  font-weight: 600;
}

.score-label {
  color: #495057;
  margin-right: 8px;
}

.score-value {
  font-size: 1.1rem;
  font-weight: 700;
}

.score-high {
  color: #28a745;
}

.score-medium {
  color: #ffc107;
}

.score-low {
  color: #dc3545;
}

.card-header {
  font-size: 1.25rem;
  font-weight: 600;
  padding: 12px 20px;
}

.score-category {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
}

.category-title {
  font-size: 1.1rem;
  margin-bottom: 10px;
  color: #343a40;
}

.score-details {
  background-color: white;
}

.score-name {
  font-weight: 600;
}

.score-number {
  font-size: 1.1rem;
  font-weight: 700;
  color: #2196f3;
}

.score-explanation {
  color: #6c757d;
}

.phrase-item {
  background-color: #f8f9fa;
  border-radius: 8px;
}

.speaker-badge {
  padding: 5px 12px;
  border-radius: 30px;
  font-weight: 600;
  font-size: 0.8rem;
  color: white;
}

.badge-pilot {
  background-color: #fd7e14;
}

.badge-atco {
  background-color: #6610f2;
}

.status-badge {
  padding: 5px 12px;
  border-radius: 30px;
  font-weight: 600;
  font-size: 0.8rem;
  color: white;
}

.status-success {
  background-color: #28a745;
}

.status-error {
  background-color: #dc3545;
}

.status-neutral {
  background-color: #6c757d;
}

.phrase-text {
  font-size: 1.1rem;
  line-height: 1.5;
}

.phrase-rule, .phrase-error {
  background-color: rgba(0, 0, 0, 0.03);
  border-radius: 4px;
}

.rule-title, .error-title {
  font-weight: 600;
  font-size: 0.9rem;
}

.rule-text, .error-text {
  font-size: 0.95rem;
  color: #495057;
}

.score-progress-container {
  width: 100%;
  height: 8px;
  background-color: #e9ecef;
  border-radius: 4px;
  margin-top: 8px;
  overflow: hidden;
}

.score-progress-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}

.score-progress-bar.score-high {
  background-color: #28a745;
}

.score-progress-bar.score-medium {
  background-color: #ffc107;
}

.score-progress-bar.score-low {
  background-color: #dc3545;
}

.keyword-badge {
  display: inline-block;
  background-color: #e9ecef;
  color: #495057;
  padding: 4px 10px;
  margin-right: 8px;
  margin-bottom: 8px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.text-success {
  color: #28a745;
}

.text-danger {
  color: #dc3545;
}

.overall-score-container {
  background-color: #f0f8ff;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.overall-score {
  background-color: white;
}

.overall-feedback {
  font-style: italic;
  color: #495057;
  border-top: 1px solid #e9ecef;
  padding-top: 10px;
  margin-top: 10px;
}

.list-group-item {
  font-size: 0.9rem;
  padding: 0.5rem 1rem;
}
</style>
