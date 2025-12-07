<template>
  <li class="audio-item list-group-item">
    <div class="audio-header d-flex justify-content-between align-items-center">
      <div>
        <h5 class="audio-title">Audio: {{ audio.file_name }}</h5>
        <p v-if="!expanded"><strong>Status:</strong> <span :class="['status-badge', statusClass]"> {{ formatStatus(audio.status) }}</span></p>
      </div>
      <div class="audio-buttons">
        <button @click="retryTranscription" class="btn btn-warning">Retry Transcription</button>
        <button @click="deleteAudio" class="btn btn-danger">Delete</button>
        <button @click="expanded = !expanded" class="btn btn-outline-secondary btn-sm" title="Expand/Collapse">
          <i :class="expanded ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
        </button>
      </div>
    </div>


    <div v-if="expanded" class="mt-3">
      <audio :src="audio.file_url" controls class="audio-player mb-3"></audio>

      <p><strong>Status:</strong> <span :class="statusClass">{{ formatStatus(audio.status) }}</span></p>
      <div class="audio-dates">
        <p><strong>Transcription Date:</strong> {{ formattedTranscriptionDate }}</p>
        <p><strong>Upload Date:</strong> {{ formattedUploadDate }}</p>
      </div>

      <div class="audio-texts" v-if="audio.status !== 'cancelled'">
        <div v-if="audio.speech_segments && audio.speech_segments.length > 0 && audio.status == 'processed'">
          <AudioSegment v-for="segment in audio.speech_segments" :key="segment.id" :segment="segment"
          @segment-deleted="forwardSegmentDeleted" @segmentUpdated="forwardSegmentUpdate"/>
        </div>
        <p v-else-if="audio.speech_segments.length == 0">No segments available.</p>

      </div>
      <div v-else>
        <p><strong>Transcription:</strong> Transcription was cancelled.</p>
      </div>
    </div>
  </li>
</template>

<script setup lang="ts">
import { reactive, computed, ref } from 'vue'
import axios from 'axios'
import { format } from 'date-fns'
import { useToast } from 'vue-toastification'
import AudioSegment from '@/components/AudioSegment.vue'

const props = defineProps<{
  audio: {
    id: string;
    file: string;
    file_name: string;
    file_url: string;
    status: string;
    transcription_date: string;
    upload_date: string;
    showButtons: boolean;
    transcription_group: string;
    speech_segments: {
      id: string;
      audio: string;
      text: string;
      modified_text: string;
      speaker_type: string;
      order: number;
      segment_file: string;
      segment_file_url: string;
    }[];
  };
  groupStatus: string;
}>();

const toast = useToast()
const expanded = ref(false)

// Definir los emits
const emit = defineEmits(['audioDeleted', 'audio-retried', 'segment-updated', 'segment-deleted']);

// Crear una copia local de audio para modificar
const localAudio = reactive({
  ...props.audio,
})

const forwardSegmentUpdate = (data: any) => {
  emit('segment-updated', data);
};

const forwardSegmentDeleted = (segmentId: string) => {
  // Remove the segment from the array of segments
  emit('segment-deleted', segmentId);
}

const deleteAudio = async () => {
  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL;
    await axios.delete(`${djangourl}audios/delete/${localAudio.id}/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })
    toast.success('Audio deleted successfully!')
    emit('audioDeleted', localAudio.id)
  } catch (error) {
    console.error('Error deleting audio:', error)
    toast.error('Error deleting audio.')
  }
}

const retryTranscription = async () => {
  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL;
    await axios.post(`${djangourl}transcribe/${localAudio.id}/`, {}, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    // Emitir evento para notificar al padre
    emit('audio-retried');
    toast.success('Transcription retry initiated successfully!');
  } catch (error) {
    console.error('Error retrying transcription:', error);
    toast.error('Error retrying transcription.');
  }
};



// Computed properties para formatear las fechas
const formattedTranscriptionDate = computed(() => {
  return localAudio.transcription_date ? format(new Date(localAudio.transcription_date), 'PPpp') : 'N/A'
})

const formattedUploadDate = computed(() => {
  return localAudio.upload_date ? format(new Date(localAudio.upload_date), 'PPpp') : 'N/A'
})

const statusClass = computed(() => {
  switch (props.audio.status) {
    case 'processed':
      return 'status-success'
    case 'failed':
      return 'status-error'
    case 'in_process':
      return 'status-processing'
    default:
      return 'status-default'
  }
})

function formatStatus(status: string): string {
  return status
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
</script>

<style scoped>
.audio-item {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 15px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  position: relative;
}

.audio-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.audio-buttons {
  display: flex;
  gap: 10px;
}

.audio-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #2196f3;
}

.audio-title {
  font-size: 1.5rem;
  margin-bottom: 15px;
  color: #2196f3;
  font-weight: 600;
}

.audio-player {
  width: 100%;
  max-width: 600px;
  margin: 15px 0;
  border-radius: 8px;
}

.audio-texts p {
  font-size: 1rem;
  color: #555;
  margin-bottom: 10px;
}

.audio-texts strong {
  color: #333;
  font-weight: 600;
}

.audio-dates p {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 8px;
}

.audio-dates strong {
  color: #444;
  font-weight: 600;
}

textarea {
  resize: none;
  overflow: hidden;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: white;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

textarea:focus {
  border-color: #2196f3;
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.2);
  outline: none;
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

.btn-success:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
}

.btn-secondary {
  background: linear-gradient(45deg, #757575, #616161);
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(117, 117, 117, 0.3);
}

.btn-secondary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(117, 117, 117, 0.4);
}

.btn-warning {
  background: linear-gradient(45deg, #ff9800, #f57c00);
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(255, 152, 0, 0.3);
}

.btn-warning:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 152, 0, 0.4);
}

.btn-danger {
  background: linear-gradient(45deg, #ff5252, #f44336);
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(244, 67, 54, 0.3);
  padding: 8px 15px;
  font-size: 12px;
}

.btn-danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(244, 67, 54, 0.4);
}

.form-control {
  margin: 15px 0;
}

.status-success {
  color: #4caf50;
  font-weight: 600;
}

.status-error {
  color: #f44336;
  font-weight: 600;
}

.status-processing {
  color: #2196f3;
  font-weight: 600;
}

.status-default {
  color: #757575;
  font-weight: 600;
}

/* Estilos para el selector de tipo de hablante */
.speaker-type-selector {
  margin: 10px 0;
  padding: 10px 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border-left: 3px solid #2196f3;
}

.speaker-select {
  max-width: 150px;
  padding: 6px 12px;
  font-size: 0.9rem;
  border-radius: 6px;
  border: 1px solid #d1d9e6;
  background-color: white;
  color: #495057;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.speaker-select:focus {
  border-color: #2196f3;
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.15);
  outline: none;
}

.speaker-select option {
  padding: 10px;
}

/* Estilos para el botón de validación */
.btn-primary {
  background: linear-gradient(45deg, #2196f3, #1976d2);
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(33, 150, 243, 0.4);
}

.btn-primary:disabled {
  background: linear-gradient(45deg, #b0bec5, #90a4ae);
  cursor: not-allowed;
  opacity: 0.7;
}

.text-muted {
  font-size: 0.8rem;
  color: #757575;
  font-style: italic;
}
</style>
