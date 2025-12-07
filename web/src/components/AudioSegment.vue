<template>
  <div class="speech-segment">
  <div class="d-flex justify-content-between align-items-center mb-2 audio-actions">
    <audio :src="localSegment.segment_file_url" controls class="audio-player"></audio>
    <button @click="deleteSegment" class="btn btn-danger">Delete segment</button>
  </div>


    <p><strong>Transcription:</strong> {{ segment.text }}</p>

    <label><strong>Edit transcription:</strong></label>
    <textarea
      v-model="localSegment.modified_text"
      class="form-control mb-2"
    ></textarea>

    <div class="d-flex align-items-center speaker-type-selector mb-3">
      <label class="me-2"><strong>Speaker role: </strong></label>
      <select v-model="localSegment.speaker_type"  class="form-select speaker-select">
        <option value="">Select role</option>
        <option value="pilot">Pilot</option>
        <option value="atco">ATCO</option>
        <option value="other">Other</option>
      </select>
    </div>

    <div v-if="hasChanges">
      <button class="btn btn-success me-2" @click="saveChanges">Save</button>
      <button class="btn btn-secondary me-2" @click="discardChanges">Discard</button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { AudioSegment } from '@/types';
import axios from 'axios';
import { useToast } from 'vue-toastification';

const toast = useToast();

const props = defineProps<{
  segment: AudioSegment;
}>();

// Evento para notificar al padre que se borró este segmento
const emit = defineEmits(['segmentDeleted', 'segmentUpdated']);


const localSegment = ref<AudioSegment>({ ...props.segment });
const originalSegment = ref<AudioSegment>({ ...props.segment });

const hasChanges = computed(() =>
  localSegment.value.modified_text !== originalSegment.value.modified_text ||
  localSegment.value.speaker_type !== originalSegment.value.speaker_type
);

const saveChanges = async () => {
  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL;
    await axios.patch(`${djangourl}segments/update/${localSegment.value.id}/`, {
      modified_text: localSegment.value.modified_text,
      speaker_type: localSegment.value.speaker_type,
    }, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    toast.success('Updated successfully!');
    originalSegment.value = { ...localSegment.value };

    emit('segmentUpdated', {
      id: localSegment.value.id,
      modified_text: localSegment.value.modified_text,
      speaker_type: localSegment.value.speaker_type,
    });

  } catch (error) {
    console.error('Error updating:', error);
    toast.error('Error updating.');
  }
};

function discardChanges() {
  localSegment.value = { ...originalSegment.value };
}

async function deleteSegment() {
  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL;
    await axios.delete(`${djangourl}segments/delete/${localSegment.value.id}/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    toast.success('Segment deleted successfully!');
    // Emitimos evento para que el padre pueda actualizar el listado
    emit('segmentDeleted', localSegment.value.id);
  } catch (error) {
    console.error('Error deleting segment:', error);
    toast.error('Error deleting segment.');
  }
}
</script>

<style scoped>
.speech-segment {
  background-color: #ffffff;
  border: 1px solid #e0e6ed;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
  position: relative;
  font-family: 'Inter', sans-serif;
}

.audio-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.audio-player {
  width: 100%;
  max-width: 400px;
  margin-right: 10px;
}

.btn-danger {
  position: static; /* importante para evitar conflictos con 'absolute' */
  padding: 8px 15px;
  font-size: 12px;
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
</style>
