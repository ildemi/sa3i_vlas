<template>
  <div class="login-container">
    <form class="login-form" @submit.prevent="handleLogin">
      <h1 class="form-title">Welcome</h1>
      <div class="form-group">
        <label class="form-label" for="username">Username</label>
        <input id="username" v-model="username" type="text" class="form-input" required />
      </div>
      <div class="form-group">
        <label class="form-label" for="password">Password</label>
        <input id="password" v-model="password" type="password" class="form-input" required />
      </div>
      <button type="submit" class="login-button">Log In</button>
      <router-link to="/register" class="register-link">Don't have an account? Register here</router-link>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'
import { useToast } from 'vue-toastification'

const username = ref('')
const password = ref('')
const router = useRouter()
const authStore = useAuthStore()
const toast = useToast() // Inicializa el toast

onMounted(async () => {
  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL;
    // const response = await axios.get(djangourl + 'login-test/')

    // const { access, refresh } = response.data

    // localStorage.setItem('token', access)
    // localStorage.setItem('refreshToken', refresh)

    // authStore.login()

    router.push('/')
  } catch (error) {
    console.error('Error en login de pruebas:', error)
    toast.error('No se pudo iniciar sesión automáticamente')
  }
})

async function handleLogin() {
  if (username.value && password.value) {
    try {
      // Enviar los datos de login al backend (API Django)
      // axios.defaults.baseURL = import.meta.env.VITE_DJANGO_URL;
      const response = await axios.post('login/', {
        username: username.value,
        password: password.value,
      })

      const { access } = response.data
      const { refresh } = response.data

      // Guardamos el token en localStorage
      localStorage.setItem('token', access)
      localStorage.setItem('refreshToken', refresh)

      // Actualizamos el estado de la autenticación
      authStore.login()

      // Redirigimos al home
      router.push('/')

    } catch (error) {
      console.error('Login error:', error)
      toast.error('Credenciales incorrectas') // Muestra un toast de error
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.login-form {
  background: white;
  padding: 2.5rem;
  border-radius: 12px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  transition: transform 0.3s ease;
}

.login-form:hover {
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

.login-button {
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

.login-button:hover {
  background-color: #1976d2;
  transform: translateY(-1px);
}

.login-button:active {
  transform: translateY(1px);
}

.login-button:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}

.register-link {
  display: block;
  text-align: center;
  color: #2196f3;
  text-decoration: none;
  font-weight: 500;
  margin-top: 1rem;
  transition: all 0.3s ease;
}

.register-link:hover {
  color: #1976d2;
  text-decoration: underline;
}
</style>
