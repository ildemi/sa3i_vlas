import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { useRouter } from 'vue-router' // Importa useRouter

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false)
  const token = ref<string | null>(localStorage.getItem('token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))
  const router = useRouter() // Inicializa el router

  // Watcher para actualizar el estado cuando el token cambie en localStorage
  watch(token, (newToken) => {
    if (newToken) {
      isAuthenticated.value = true
    } else {
      isAuthenticated.value = false
    }
  }, { immediate: true })

  // Función para iniciar sesión
  function login() {
    const storedToken = localStorage.getItem('token')

    if (storedToken) {
      token.value = storedToken
    }

    const storedRefreshToken = localStorage.getItem('refreshToken')
    if (storedRefreshToken) {
      refreshToken.value = storedRefreshToken
    }
  }

  // Función para cerrar sesión
  function logout() {
    isAuthenticated.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    token.value = null
    refreshToken.value = null
    router.push('/login') // Redirige al usuario al login
  }

  return { isAuthenticated, login, logout }
})
