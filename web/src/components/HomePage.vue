<template>
  <div class="container">
    <div class="upload-section">
      <h2>Upload Audio Files</h2>

      <!-- Campo para ingresar el nombre del grupo -->
      <label for="groupName">Group Name:</label>
      <input type="text" id="groupName" v-model="groupName" placeholder="Enter group name" />

      <!-- Contenedor para los botones -->
      <div class="button-container">
        <button
          @click="submitFiles"
          class="btn btn-primary"
          :disabled="!groupName || audioFiles.length === 0 || loading">
          Submit
        </button>
        <button
          @click="resetForm"
          class="btn btn-secondary"
          :disabled="(!groupName && audioFiles.length === 0) || loading">
          Cancel
        </button>
      </div>

      <div v-if="loading" class="overlay">
        <div class="spinner-wrapper">
          <span class="loader"></span>
          <p>Uploading...</p>
        </div>
      </div>

      <!-- Input para seleccionar archivos -->
      <label class="file-input-label" :class="{ disabled: loading }">
        <input
          type="file"
          @change="onFilesChange"
          accept="audio/*"
          multiple
          class="file-input"
          :disabled="loading"
        />
        <span>Select audio files</span>
      </label>

      <!-- Mostrar los archivos seleccionados -->
      <div v-if="audioFiles.length > 0" class="file-list">
        <p><strong>Selected Files:</strong></p>
        <ul>
          <li v-for="(file, index) in audioFiles" :key="index" class="file-item">
            <span>{{ file.name }}</span>
            <button @click="removeFile(index)" class="btn btn-danger btn-sm" :disabled="loading">Remove</button>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useToast } from 'vue-toastification'

const router = useRouter()
const toast = useToast()

const audioFiles = ref<File[]>([])
const groupName = ref('')

// Estado para controlar spinner
const loading = ref(false)

const onFilesChange = (event: Event) => {
  if (loading.value) return
  const input = event.target as HTMLInputElement
  if (input.files) {
    const selected = Array.from(input.files).filter(file => file.type.startsWith('audio/'))
    const uniqueFiles = selected.filter(newFile =>
      !audioFiles.value.some(existing =>
        existing.name === newFile.name && existing.size === newFile.size
      )
    )
    audioFiles.value.push(...uniqueFiles)
  }
}

const removeFile = (index: number) => {
  if (loading.value) return
  audioFiles.value.splice(index, 1)
}

const submitFiles = async () => {
  if (audioFiles.value.length === 0 || !groupName.value) return

  loading.value = true

  try {
    const formData = new FormData()
    audioFiles.value.forEach(file => {
      formData.append('file', file)
    })
    formData.append('group_name', groupName.value)

    const djangourl = import.meta.env.VITE_DJANGO_URL
    const response = await axios.post(djangourl + 'create-transcription-group/', formData, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'multipart/form-data',
      },
    })

    const groupId = response.data.id
    router.push({ name: 'group-detail', params: { groupId } })

  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      const errorData = error.response.data;
      if (errorData.error) {
        toast.error(errorData.error);
      } else {
        toast.error('An error occurred while uploading files.');
      }
    } else {
      console.error('Error uploading files:', error)
      toast.error('An unexpected error occurred.');
    }
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  if (loading.value) return
  audioFiles.value = []
  groupName.value = ''
}
</script>

<style scoped>
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

/* Opcional: deshabilitar estilo para input cuando carga */
.file-input-label.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.container {
  width: 95%;
  max-width: 1200px;
  margin: 2rem auto;
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.upload-section {
  text-align: center;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  position: relative;
  height: 100%;
  width: 100%;
  margin: 0;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
}

.upload-section h2 {
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

.file-input-label {
  display: inline-block;
  padding: 15px 30px;
  background: linear-gradient(45deg, #4caf50, #45a049);
  color: white;
  border-radius: 50px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
}

.file-input-label:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
}

.file-input {
  display: none;
}

#groupName {
  padding: 1rem 1.5rem;
  font-size: 16px;
  width: 100%;
  max-width: 800px;
  border-radius: 8px;
  border: 2px solid #e0e0e0;
  transition: all 0.3s ease;
  background: white;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

#groupName:focus {
  border-color: #2196f3;
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.2);
  outline: none;
}

.file-list {
  margin-top: 1.5rem;
  text-align: left;
  width: 100%;
  max-width: 800px;
  background: white;
  padding: 1.5rem;
  border-radius: 15px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: #f8f9fa;
  margin-bottom: 8px;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.file-item:hover {
  transform: translateX(5px);
  background: #f0f4f8;
}

.file-item button {
  background: linear-gradient(45deg, #ff5252, #f44336);
  color: white;
  border: none;
  border-radius: 50px;
  padding: 8px 15px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.file-item button:hover {
  background: linear-gradient(45deg, #f44336, #d32f2f);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(244, 67, 54, 0.3);
}

.btn-primary {
  background: linear-gradient(45deg, #2196f3, #1976d2);
  color: white;
  border: none;
  padding: 15px 40px;
  border-radius: 50px;
  font-size: 16px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
}

.btn-primary:not(:disabled):hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(33, 150, 243, 0.4);
}

.btn-primary:disabled {
  background: linear-gradient(45deg, #b0bec5, #90a4ae);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 2rem;
}

.loading-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #2196f3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  box-shadow: 0 4px 10px rgba(33, 150, 243, 0.2);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Animaciones para elementos que aparecen */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.file-item {
  animation: fadeInUp 0.3s ease forwards;
}

/* Eliminar el efecto glass morphism que ya no necesitamos */
.container {
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}

/* Eliminar la animación de elevación */
.container:hover {
  transform: none;
}

/* Añadir estilos para el nuevo botón y contenedor */
.button-container {
  display: flex;
  gap: 1rem;
  margin: 1rem 0;
}

.btn-secondary {
  background: linear-gradient(45deg, #757575, #616161);
  color: white;
  border: none;
  padding: 15px 40px;
  border-radius: 50px;
  font-size: 16px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(117, 117, 117, 0.3);
}

.btn-secondary:not(:disabled):hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(117, 117, 117, 0.4);
}

.btn-secondary:disabled {
  background: linear-gradient(45deg, #b0bec5, #90a4ae);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
</style>
