<template>
  <div class="account-container">
    <h1>Change Password</h1>
    <form @submit.prevent="updatePassword" class="account-info">
      <div v-if="errorMessages.length" class="error-box">
        <ul>
          <li v-for="(error, index) in errorMessages" :key="index">{{ error }}</li>
        </ul>
      </div>
      <div class="info-group">
        <label for="current-password">Current Password:</label>
        <input id="current-password" v-model="passwordData.currentPassword" type="password" class="form-control"
          required />
      </div>
      <div class="info-group">
        <label for="new-password">New Password:</label>
        <input id="new-password" v-model="passwordData.newPassword" type="password" class="form-control" required />
      </div>
      <div class="info-group">
        <label for="confirm-password">Confirm Password:</label>
        <input id="confirm-password" v-model="passwordData.confirmPassword" type="password" class="form-control"
          required />
      </div>
      <div class="button-group">
        <button type="submit" class="btn btn-primary mt-3">Save Changes</button>
        <button type="button" @click="discardChanges" class="btn btn-secondary mt-3 ml-2">Discard Changes</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'
import eventBus from '@/eventBus'
import { useRouter } from 'vue-router'

const router = useRouter()
const toast = useToast()
const passwordData = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const errorMessages = ref<string[]>([])

async function updatePassword() {
  errorMessages.value = [] // Limpiar mensajes de error antes de intentar actualizar

  try {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }

    const djangourl = import.meta.env.VITE_DJANGO_URL;
    const response = await axios.put(djangourl + 'change-password/', {
      old_password: passwordData.value.currentPassword,
      new_password: passwordData.value.newPassword,
      confirm_password: passwordData.value.confirmPassword
    }, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    toast.success(response.data.detail)

    // Emitir evento para cambiar a la vista de perfil después de guardar
    eventBus.emit('navigate', 'Account')

  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      const errorData = error.response.data;
      if (Array.isArray(errorData.detail)) {
        // Añadir cada mensaje de error al array de mensajes de error
        errorMessages.value = errorData.detail;
      } else if (typeof errorData.detail === 'string') {
        errorMessages.value.push(errorData.detail);
      } else {
        errorMessages.value.push('An unknown error occurred.');
      }
    } else {
      console.error('Error updating password:', error)
      errorMessages.value.push('There was an error updating your password.')
    }
  }
  passwordData.value = {
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
}

function discardChanges() {
  toast.info('Changes discarded.')
  eventBus.emit('navigate', 'Account')
}
</script>

<style scoped>
.error-box {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  padding: 10px;
  margin-bottom: 15px;
  border-radius: 5px;
}

.account-container {
  flex: 1;
  max-width: 800px;
  margin-left: 15px;
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

h1 {
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

.account-info {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.info-group {
  display: grid;
  grid-template-columns: 150px 1fr;
  align-items: center;
  padding: 1rem;
  background: #f7f7f7;
  border-radius: 8px;
}

label {
  font-weight: 600;
  color: #666;
}

input {
  margin: 0;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  color: #333;
}

.button-group {
  display: flex;
  gap: 10px;
}

.btn {
  align-self: flex-start;
}
</style>
