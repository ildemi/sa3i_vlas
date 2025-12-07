<template>
  <div class="container">
    <div class="card shadow-sm">
      <div class="card-body">
        <router-link to="/history" class="btn btn-outline-primary mb-1">Back to History</router-link>
        <h2 class="card-title text-center mb-2">{{ group.group_name }}</h2>

        <!-- Botón para abrir el modal -->
        <div class="text-center mb-3">
          <button class="btn btn-success" @click="showModal = true">Add Audio Files</button>
        </div>

        <!-- Modal -->
        <div class="modal fade show d-block" tabindex="-1" role="dialog" v-if="showModal">
          <div class="modal-dialog modal-dialog-centered" role="document">
            <div class="modal-content shadow">

              <div class="modal-header">
                <h5 class="modal-title">Upload Audio Files</h5>
                <button type="button" class="btn-close" @click="closeModal" aria-label="Close"></button>
              </div>

              <div class="modal-body">
                <!-- Input para seleccionar archivos -->
                <label class="form-label w-100">
                  <input type="file" @change="onFilesChange" accept="audio/*" multiple class="form-control" />
                </label>

                <!-- Lista de archivos seleccionados -->
                <div v-if="audioFiles.length > 0" class="mt-3">
                  <p><strong>Selected Files:</strong></p>
                  <ul class="list-group">
                    <li v-for="(file, index) in audioFiles" :key="index"
                      class="list-group-item d-flex justify-content-between align-items-center">
                      <span>{{ file.name }}</span>
                      <button @click="removeFile(index)" class="btn btn-outline-danger btn-sm">Remove</button>
                    </li>
                  </ul>
                </div>

                <div v-else class="text-muted text-center mt-2">No files selected.</div>
              </div>

              <div class="modal-footer">
                <button class="btn btn-primary" @click="submitFiles" :disabled="audioFiles.length === 0">Submit</button>
              </div>

            </div>
          </div>
        </div>

        <!-- Modal para ordenar audios -->
        <div class="modal fade show d-block" tabindex="-1" role="dialog" v-if="showOrderModal">
          <div class="modal-dialog modal-dialog-centered" role="document">
            <div class="modal-content shadow">

              <div class="modal-header">
                <h5 class="modal-title">Order Audio Files</h5>
                <button type="button" class="btn-close" @click="closeOrderModal" aria-label="Close"></button>
              </div>

              <div class="modal-body">
                <draggable v-model="audiosOrderForSorting" item-key="id" tag="ul" class="list-group" handle=".drag-handle">
                  <template #item="{ element, index }">
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                      <div class="drag-handle me-2">
                         <i class="bi bi-grip-vertical fs-5"></i>
                      </div>

                      <span class="flex-grow-1"> {{ element.file_name || 'Audio' }}</span>
                      <div>
                        <button class="btn btn-sm btn-outline-primary me-1" @click="moveUp(index)" :disabled="index === 0">↑</button>
                        <button class="btn btn-sm btn-outline-primary" @click="moveDown(index)" :disabled="index === audiosOrderForSorting.length - 1">↓</button>
                      </div>
                    </li>
                  </template>
                </draggable>
              </div>

              <div class="modal-footer">
                <button class="btn btn-secondary" @click="closeOrderModal">Cancel</button>
                <button class="btn btn-primary" @click="saveOrder" :disabled="isValidating">Save Order & Validate</button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="showOrderModal" class="modal-backdrop fade show"></div>

        <!-- Overlay al mostrar modal -->
        <div v-if="showModal" class="modal-backdrop fade show"></div>

        <div v-if="loading" class="overlay">
          <div class="spinner-wrapper">
            <span class="loader"></span>
            <p>Uploading...</p>
          </div>
        </div>

        <!-- The cancel button is only shown when there are pending or processing audios -->
        <div class="d-flex justify-content-end mb-3">
          <button v-if="hasPendingOrProcessingAudios && showCancelButton" @click="cancelGroupTranscriptions"
            class="btn btn-danger" :disabled="isCancelling">
            <span v-if="isCancelling" class="spinner-border spinner-border-sm me-2" role="status"></span>
            {{ isCancelling ? 'Cancelling...' : 'Cancel All Transcriptions' }}
          </button>
        </div>

        <div v-if="group.audios.length === 0" class="alert alert-warning text-center">
          No audios found for this group.
        </div>

        <div v-else>
          <!-- Validation button -->
          <div v-if="canValidateGroup" class="d-flex justify-content-center mb-4">
            <button @click="openOrderModal" class="btn btn-primary btn-lg" :disabled="isValidating">
              <span v-if="isValidating" class="spinner-border spinner-border-sm me-2" role="status"></span>
              {{ isValidating ? 'Validating...' : 'Validate Conversation' }}
            </button>

          </div>
          <div v-if="validationMessage" class="d-flex justify-content-center mb-3">
            <div class="validation-message">{{ validationMessage }}</div>
          </div>

          <!-- List of audios -->
          <ul class="list-group list-group-flush">
            <audio-detail v-for="audio in sortedAudios" :key="audio.id" :audio="audio" :group-status="group.status"
              class="list-group-item" @audio-deleted="handleAudioDeleted" @audio-retried="handleRetry"  @segmentUpdated="handleSegmentUpdate" @segment-deleted="handleSegmentDeleted"/>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import AudioDetail from '@/components/AudioDetail.vue'
import { useToast } from 'vue-toastification'
import draggable from 'vuedraggable'
import type { TranscriptionGroup, AudioFile } from '@/types'

const group = ref<TranscriptionGroup>({
  group_id: '',
  status: '',
  audios: [],
  group_name: '',
})

const route = useRoute()
const isCancelling = ref(false)
const showCancelButton = ref(false)
const updateInterval = ref<ReturnType<typeof setInterval> | null>(null)
const isValidating = ref(false)
const validationMessage = ref('')
const toast = useToast()
const audioFiles = ref<File[]>([])
const showModal = ref(false)
const loading = ref(false)
const showOrderModal = ref(false)

const sortedAudios = computed(() => {
  return [...group.value.audios].sort((a, b) => a.order - b.order)
})

const audiosOrderForSorting = ref([...sortedAudios.value])

const openOrderModal = () => {
  audiosOrderForSorting.value = [...sortedAudios.value]  // Clona el array actual
  showOrderModal.value = true
}

const moveUp = (index: number) => {
  if (index === 0) return
  const temp = audiosOrderForSorting.value[index - 1]
  audiosOrderForSorting.value[index - 1] = audiosOrderForSorting.value[index]
  audiosOrderForSorting.value[index] = temp
}

const moveDown = (index: number) => {
  if (index === audiosOrderForSorting.value.length - 1) return
  const temp = audiosOrderForSorting.value[index + 1]
  audiosOrderForSorting.value[index + 1] = audiosOrderForSorting.value[index]
  audiosOrderForSorting.value[index] = temp
}

const closeOrderModal = () => {
  showOrderModal.value = false
}

const saveOrder = async () => {
  if (!route.params.groupId) {
    toast.error('No group ID found.')
    return
  }

  isValidating.value = true // Reusar isValidating para bloquear botones

  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL
    const groupId = route.params.groupId

    // Crear payload con nuevo orden [{id: audio.id, order: índice + 1}]
    const newOrderPayload = audiosOrderForSorting.value.map((audio, index) => ({
      id: audio.id,
      order: index + 1,
    }))

    // Petición para actualizar orden
    await axios.post(
      `${djangourl}update-audio-order/${groupId}/`,  // O la URL que tengas para esto
      { audios: newOrderPayload },
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      }
    )

    toast.success('Order saved successfully.')

    // Actualizar localmente el grupo con nuevo orden
    group.value.audios.forEach(audio => {
      const newAudio = newOrderPayload.find(a => a.id === audio.id)
      if (newAudio) {
        audio.order = newAudio.order
      }
    })

    // Cerrar modal
    showOrderModal.value = false

    // Esperar un poco para que Vue detecte cambios
    await new Promise(r => setTimeout(r, 100))

    // Lanzar la validación
    await validateTranscriptionGroup()

  } catch (error) {
    console.error('Error saving order:', error)
    toast.error('Failed to save order. Please try again.')
    isValidating.value = false
  }
}

const handleSegmentUpdate = (payload: { id: string; modified_text: string; speaker_type: string }) => {
  const { id, modified_text, speaker_type } = payload;

  for (const audio of group.value.audios) {
    const segment = audio.speech_segments.find(s => s.id === id);
    if (segment) {
      segment.modified_text = modified_text;
      segment.speaker_type = speaker_type;
    }
  }
};

const handleSegmentDeleted = (segmentId: string) => {
  // Buscar el audio correspondiente
  for (const audio of group.value.audios) {
    const segmentIndex = audio.speech_segments.findIndex(s => s.id === segmentId);
    if (segmentIndex !== -1) {
      audio.speech_segments.splice(segmentIndex, 1);
      break; // Salir del bucle una vez encontrado y eliminado
    }
  }
};

// Función para añadir archivos de audio a un grupo
const submitFiles = async () => {
  if (audioFiles.value.length === 0) {
    return // No hacer nada si no hay archivos
  }

  const groupId = route.params.groupId
  if (!groupId) {
    toast.error('No se ha especificado el grupo.')
    return
  }
  loading.value = true

  const formData = new FormData()
    audioFiles.value.forEach(file => {
    formData.append('file', file)
  })

  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL
    await axios.post(
      `${djangourl}add-audio-to-group/${groupId}/`,
      formData,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'multipart/form-data',
        },
      }
    )

    toast.success('Files added successfully.')
    audioFiles.value = [] // Limpiar la lista de archivos después de subir
    showModal.value = false // Cierra el modal después de subir los archivos
    await loadGroup() // actualiza la lista sin recargar la página

  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      const errorData = error.response.data
      if (errorData.error) {
        toast.error(errorData.error)
      } else {
        toast.error('An error occurred while uploading the files.')
      }
    } else {
      console.error('Error uploading files:', error)
      toast.error('Ocurrió un error inesperado.')
    }
  }
  loading.value = false
}

// Función para cerrar el modal
const closeModal = () => {
  audioFiles.value = []
  showModal.value = false
}

// Función para manejar el cambio de archivos
async function onFilesChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) {
    // Filtrar solo los archivos de tipo audio
    const selectedFiles = Array.from(input.files).filter(file => file.type.startsWith('audio/'))

    // Agregar nuevos archivos a la lista de archivos seleccionados sin eliminar los anteriores
    audioFiles.value.push(...selectedFiles)
  }
}

// Función para eliminar un archivo de la lista de seleccionados
const removeFile = (index: number) => {
  audioFiles.value.splice(index, 1)
}

const hasPendingOrProcessingAudios = computed(() => {
  return group.value.audios.some(audio =>
    audio.id &&
    (audio.status === 'pending' || audio.status === 'in_process')
  )
})

const canValidateGroup = computed(() => {
  // validation can only occur if:
  // 1. all audios are processed
  // 2. there are audios in the group
  // 3. the group is not in the process of validation or already validated
  // 4. all speech segments have a valid speaker type (either 'atco' or 'pilot')
  const allSegmentsHaveSpeakerType = group.value.audios.every(audio =>
    audio.speech_segments.every(segment => {
      const speaker = segment.speaker_type?.toLowerCase() || '';
      return speaker === 'atco' || speaker === 'pilot';
    })
  );

  return group.value.status.toLowerCase() === 'processed' &&
    group.value.audios.length > 0 &&
    !isValidating.value &&
    (!group.value.validation_status ||
      group.value.validation_status.toLowerCase() !== 'in_process') &&
    allSegmentsHaveSpeakerType;
});



const validateTranscriptionGroup = async () => {
  try {
    if (!route.params.groupId) {
      console.error('Group ID not found')
      return
    }

    isValidating.value = true
    validationMessage.value = ''

    const djangourl = import.meta.env.VITE_DJANGO_URL
    const groupId = route.params.groupId

    const response = await axios.post(
      `${djangourl}validate-transcription-group/${groupId}/`,
      { model: 'phi4' },
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      }
    )

    if (response.status === 202) {
      validationMessage.value = 'Validation started successfully.'
      group.value.validation_status = 'in_process'
    } else {
      validationMessage.value = 'Error starting validation.'
      isValidating.value = false
    }
  } catch (error: any) {
    console.error('Error validating transcription group:', error)

    if (error.response) {
      validationMessage.value = `Error: ${error.response.data.detail || 'Server error'}`
    } else if (error.request) {
      validationMessage.value = 'Error: No response received from the server'
    } else {
      validationMessage.value = `Error: ${error.message}`
    }
    isValidating.value = false
  }
}

const cancelGroupTranscriptions = async () => {
  try {
    if (!route.params.groupId) {
      console.error('Group ID not found')
      return
    }

    isCancelling.value = true
    const djangourl = import.meta.env.VITE_DJANGO_URL
    const groupId = route.params.groupId

    await axios.post(
      `${djangourl}transcription-group/${groupId}/cancel/`,
      {},
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      }
    )

    await new Promise(resolve => setTimeout(resolve, 500))

    const response = await axios.get(djangourl + `transcription-group/${groupId}/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })
    group.value = response.data
    group.value.audios.forEach(audio => {
      audio.showButtons = false
    })
  } catch (error) {
    console.error('Error cancelling transcriptions:', error)
  } finally {
    isCancelling.value = false
  }
}

// Function to update the group status
const updateGroupStatus = async () => {
  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL
    const response = await axios.get(djangourl + `transcription-group/${route.params.groupId}/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })

    // Actualizar audios con los datos recibidos, incluidos speech_segments
    response.data.audios.forEach((newAudio: AudioFile) => {
    const existingAudio = group.value.audios.find(a => a.id === newAudio.id)
    if (existingAudio) {
      // Copiar todas las propiedades para no olvidar ninguna
      Object.assign(existingAudio, newAudio)

      // Asegurar que speech_segments se reemplace con nueva referencia para reactividad
      existingAudio.speech_segments = Array.isArray(newAudio.speech_segments)
        ? [...newAudio.speech_segments]
        : []

      // Asegurar que transcription_group está actualizado (siempre string)
      existingAudio.transcription_group = route.params.groupId as string
      }
    })

    // Actualizar estado del grupo
    group.value.status = response.data.status

    // Forzar actualización del array de audios (en caso Vue no detecte mutación interna)
    group.value.audios = [...group.value.audios]

    // Detener intervalo si no hay audios pendientes o procesando
    if (!hasPendingOrProcessingAudios.value) {
      stopUpdateInterval()
    }

  } catch (error) {
    console.error('Error updating group status:', error)
  }
}

// Start the update interval when there are pending or processing audios
const startUpdateInterval = () => {
  if (hasPendingOrProcessingAudios.value && !updateInterval.value) {
    updateInterval.value = setInterval(updateGroupStatus, 10000) // Update every 10 seconds
  }
}

// Stop the interval when there are no pending audios
const stopUpdateInterval = () => {
  if (updateInterval.value) {
    clearInterval(updateInterval.value)
    updateInterval.value = null
  }
}

// Modify the watch for the audio status
watch(() => hasPendingOrProcessingAudios.value, (newValue) => {
  if (newValue) {
    startUpdateInterval()
  } else {
    stopUpdateInterval()
    // If there are no pending or processing audios, hide the cancel button
    showCancelButton.value = false
  }
})

const handleAudioDeleted = (audioId: string) => {
  // Remove the audio from the array of audios
  group.value.audios = group.value.audios.filter(audio => audio.id !== audioId)
}

const loadGroup = async () => {
  const groupId = route.params.groupId
  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL;
    const response = await axios.get(djangourl + `transcription-group/${groupId}/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })
    group.value = response.data

    group.value.audios.forEach(audio => {
      audio.showButtons = false
      audio.transcription_group = groupId as string
    })

    // Mostrar botón de cancelar si hay audios pendientes
    setTimeout(() => {
      if (hasPendingOrProcessingAudios.value) {
        showCancelButton.value = true
      }
    }, 500)
  } catch (error) {
    console.error('Error fetching group details:', error)
  }
}

onMounted(async () => {
  await loadGroup()
  startUpdateInterval()
})

onUnmounted(() => {
  stopUpdateInterval()
})

const handleRetry = async () => {
  await loadGroup()
  startUpdateInterval()
}
</script>

<style scoped>
.container {
  width: 95%;
  max-width: 1200px;
  margin: 2rem auto;
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(255, 255, 255, 0.75);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.spinner-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  background-color: white;
  padding: 2rem 3rem;
  border-radius: 12px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.spinner-wrapper p {
  font-weight: bold;
  font-size: 1.1rem;
  color: #333;
}

.loader {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  position: relative;
  animation: rotate 1s linear infinite
}

.loader::before {
  content: "";
  box-sizing: border-box;
  position: absolute;
  inset: 0px;
  border-radius: 50%;
  border: 5px solid #2196f3;
  animation: prixClipFix 2s linear infinite ;
}

@keyframes rotate {
  100%   {transform: rotate(360deg)}
}

@keyframes prixClipFix {
    0%   {clip-path:polygon(50% 50%,0 0,0 0,0 0,0 0,0 0)}
    25%  {clip-path:polygon(50% 50%,0 0,100% 0,100% 0,100% 0,100% 0)}
    50%  {clip-path:polygon(50% 50%,0 0,100% 0,100% 100%,100% 100%,100% 100%)}
    75%  {clip-path:polygon(50% 50%,0 0,100% 0,100% 100%,0 100%,0 100%)}
    100% {clip-path:polygon(50% 50%,0 0,100% 0,100% 100%,0 100%,0 0)}
}
.card {
  border: none;
  box-shadow: none;
  background: transparent;
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
  padding: 12px 25px;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-radius: 50px;
  transition: all 0.3s ease;
  border: 2px solid #2196f3;
  color: #2196f3;
}

.btn-outline-primary:hover {
  background: linear-gradient(45deg, #2196f3, #1976d2);
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
  color: white;
}

.btn-danger {
  background: linear-gradient(45deg, #ff5252, #f44336);
  color: white;
  border: none;
  padding: 12px 25px;
  border-radius: 50px;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(244, 67, 54, 0.3);
}

.btn-danger:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(244, 67, 54, 0.4);
}

.btn-danger:disabled {
  background: linear-gradient(45deg, #b0bec5, #90a4ae);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
.btn {
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-radius: 50px;
  transition: all 0.3s ease;
}

.btn-success {
  background: linear-gradient(45deg, #4caf50, #45a049);
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
}
.list-group {
  margin-top: 1.5rem;
}

.list-group-item {
  border: none;
  background: #f8f9fa;
  border-radius: 10px !important;
  transition: all 0.3s ease;
}

.list-group-item:hover {
  background: #f0f4f8;
}

.alert {
  background: #fff3cd;
  color: #856404;
  border: none;
  border-radius: 10px;
  padding: 1rem;
  text-align: center;
  font-weight: 500;
}

.spinner-border {
  width: 1.2rem;
  height: 1.2rem;
}

.btn-primary {
  background: linear-gradient(45deg, #2196f3, #1976d2);
  color: white;
  border: none;
  padding: 12px 25px;
  border-radius: 50px;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(33, 150, 243, 0.4);
}

.btn-primary:disabled {
  background: linear-gradient(45deg, #b0bec5, #90a4ae);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-success {
  background: linear-gradient(45deg, #4caf50, #45a049);
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
}

.btn-success:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
}

.validation-message {
  margin-top: 10px;
  padding: 10px 15px;
  border-radius: 8px;
  background-color: #e3f2fd;
  color: #0d47a1;
  font-size: 14px;
  text-align: center;
  width: 100%;
  max-width: 600px;
}

.drag-handle {
  cursor: grab;
}
</style>
