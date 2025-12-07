<template>
  <div class="register-container">
    <form class="register-form" @submit.prevent="handleRegister">
      <h1 class="form-title">Registration</h1>
      
      <div class="form-group">
        <label class="form-label" for="username">Username *</label>
        <input id="username" v-model="formData.username" type="text" class="form-input" required />
      </div>

      <div class="form-group">
        <label class="form-label" for="email">Email *</label>
        <input id="email" v-model="formData.email" type="email" class="form-input" required />
      </div>

      <div class="form-group">
        <label class="form-label" for="first_name">First Name</label>
        <input id="first_name" v-model="formData.first_name" type="text" class="form-input" />
      </div>

      <div class="form-group">
        <label class="form-label" for="last_name">Last Name</label>
        <input id="last_name" v-model="formData.last_name" type="text" class="form-input" />
      </div>

      <div class="form-group">
        <label class="form-label" for="password">Password *</label>
        <input id="password" v-model="formData.password" type="password" class="form-input" required />
      </div>

      <div class="form-group">
        <label class="form-label" for="confirm_password">Confirm Password *</label>
        <input id="confirm_password" v-model="formData.confirm_password" type="password" class="form-input" required />
      </div>

      <button type="submit" class="register-button" :disabled="isLoading">
        {{ isLoading ? 'Registering...' : 'Register' }}
      </button>
      
      <router-link to="/login" class="login-link">Already have an account? Log in here</router-link>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'
import { useToast } from 'vue-toastification'

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()
const isLoading = ref(false)

const formData = ref({
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  password: '',
  confirm_password: ''
})

async function handleRegister() {
  if (formData.value.password !== formData.value.confirm_password) {
    toast.error('Las contraseñas no coinciden')
    return
  }

  isLoading.value = true
  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL
    const response = await axios.post(djangourl + 'register/', formData.value)

    const { access, refresh } = response.data

    // Guardamos los tokens
    localStorage.setItem('token', access)
    localStorage.setItem('refreshToken', refresh)

    // Actualizamos el estado de autenticación
    authStore.login()

    toast.success('Registro exitoso')
    router.push('/')
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Error al registrar usuario'
    toast.error(errorMessage)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 2rem;
}

.register-form {
  background: white;
  padding: 2.5rem;
  border-radius: 12px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 500px;
  transition: transform 0.3s ease;
}

.register-form:hover {
  transform: translateY(-5px);
}

.form-title {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 2rem;
  font-size: 2rem;
  font-weight: 600;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  color: #34495e;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 0.8rem;
  border: 2px solid #dcdfe6;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.form-input:focus {
  border-color: #2196f3;
  outline: none;
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
}

.register-button {
  width: 100%;
  padding: 1rem;
  background-color: #2196f3;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 1rem;
}

.register-button:hover:not(:disabled) {
  background-color: #1976d2;
  transform: translateY(-1px);
}

.register-button:active:not(:disabled) {
  transform: translateY(1px);
}

.register-button:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}

.login-link {
  display: block;
  text-align: center;
  color: #2196f3;
  text-decoration: none;
  font-weight: 500;
  margin-top: 1rem;
  transition: all 0.3s ease;
}

.login-link:hover {
  color: #1976d2;
  text-decoration: underline;
}
</style> 