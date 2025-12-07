<template>
  <div class="container my-4">
    <h2 class="text-center mb-4">Editor de Validación</h2>

    <div v-if="isLoading" class="text-center">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="mt-2">Cargando audios y transcripciones...</p>
    </div>

    <div v-else>
      <draggable v-model="audioList" item-key="id" handle=".drag-handle">
        <template #item="{ element: audio }">
          <div class="card my-3 p-3">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <div class="drag-handle text-muted"><i class="bi bi-grip-vertical fs-4"></i></div>
              <h5 class="mb-0">{{ audio.file_name }}</h5>
            </div>

            <div v-for="utterance in audio.utterances" :key="utterance.id" class="utterance-box">
              <label class="form-label fw-bold">Texto:</label>
              <textarea
                v-model="utterance.text"
                class="form-control mb-2"
                rows="2"
              ></textarea>

              <label class="form-label fw-bold">Hablante:</label>
              <select
                v-model="utterance.speaker_type"
                class="form-select form-select-sm w-auto"
              >
                <option value="">Sin especificar</option>
                <option value="atco">ATCO</option>
                <option value="pilot">Piloto</option>
              </select>
            </div>
          </div>
        </template>
      </draggable>

      <div class="text-end mt-4">
        <button @click="validateTranscriptionGroup" class="btn btn-success">
          Validar Conversación
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import draggable from 'vuedraggable'
import axios from 'axios'
import { useToast } from 'vue-toastification'

const toast = useToast()
const djangourl = import.meta.env.VITE_DJANGO_URL
const route = useRoute()
const router = useRouter()
const isValidating = ref(false)
const validationMessage = ref('')
const isLoading = ref(true)
const audioList = ref([])


onMounted(async () => {
  const groupId = route.params.group_id
  try {
    const response = await axios.get(`${djangourl}transcription-groups/${groupId}/phrases/`)
    audioList.value = response.data.audios
  } catch (error) {
    console.error('Error loading audios:', error)
    toast.error('Failed to load audio transcriptions.')
  } finally {
    isLoading.value = false
  }
})

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
      //group.value.validation_status = 'in_process'
      router.push({ name: 'history' })
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
</script>

<style scoped>
.utterance-box {
  border: 1px solid #dee2e6;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
  background-color: #f8f9fa;
}
.drag-handle {
  cursor: grab;
}
</style>
