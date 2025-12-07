<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const router = useRouter()
const route = useRoute()

const authStore = useAuthStore()

// Comprobar la validez del token en el montaje
onMounted(() => {
  const token = localStorage.getItem('token')
  if (token) {
    // Verificar si el token sigue siendo válido
    const djangourl = import.meta.env.VITE_DJANGO_URL;
    axios.get(djangourl + 'verify-token/', { headers: { Authorization: `Bearer ${token}` } })
      .then(() => {
        authStore.login()
      })
      .catch(() => {
        authStore.logout()
        router.push('/login')
      })
  } else {
    authStore.logout()
    router.push('/login')
  }
})

const showNav = computed(() => {
  return route.path !== '/login' && route.path !== '/register'
})

function logout() {
  authStore.logout()
}
</script>

<template>
  <header v-if="showNav">
    <div class="header-container">
      <RouterLink to="/" class="logo-link">
        <img src="@/assets/logo_saerco.png" alt="Saerco Logo" class="logo" />
      </RouterLink>
      <nav class="main-nav">
        <RouterLink to="/">Transcribe</RouterLink>
        <RouterLink to="/history">Saved Transcriptions</RouterLink>
        <RouterLink to="/account">Account</RouterLink>
        <RouterLink to="/wer">WER</RouterLink>
        <button @click="logout" class="nav-button logout-button">Logout</button>
      </nav>
    </div>
  </header>

  <main class="main-content">
    <RouterView />
  </main>
</template>

<style scoped>
header {
  width: 100vw;
  padding: 0.75rem 0;
  margin-bottom: 2rem;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
  left: 0;
  right: 0;
  margin-left: -50vw;
  margin-right: -50vw;
  position: relative;
  left: 50%;
  right: 50%;
}

.header-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0 2rem;
  margin: 0 auto;
}

.logo {
  width: 150px;
  height: auto;
  margin-right: 2rem;
  display: block;
}

.main-nav {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-grow: 1;
  gap: 1rem;
}

.main-nav a {
  color: var(--vt-c-text-light-1);
  font-size: 1rem;
  font-weight: 600;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  transition: all 0.3s ease;
  text-decoration: none;
}

.main-nav a:hover {
  background-color: var(--vt-c-white-mute);
  color: var(--color-heading);
  transform: translateY(-1px);
}

.main-nav a.router-link-active {
  color: #2196f3;
  background-color: rgba(33, 150, 243, 0.1);
}

.nav-button {
  color: var(--vt-c-text-light-1);
  font-size: 1rem;
  font-weight: 600;
  padding: 0.6rem 1.2rem;
  border: 2px solid var(--vt-c-divider-light-1);
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.nav-button:hover {
  background-color: var(--vt-c-text-light-1);
  color: white;
  border-color: var(--vt-c-text-light-1);
  transform: translateY(-1px);
}

.logout-button {
  margin-left: auto;
}

@media (max-width: 768px) {
  .header-container {
    padding: 0 1rem;
    flex-direction: column;
    align-items: center;
    width: 100%;
  }

  .main-nav {
    width: 100%;
    justify-content: space-evenly;
    margin-top: 1rem;
  }

  .main-nav a,
  .nav-button {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
  }
}

.logo-link,
.logo-link:focus,
.logo-link:active,
.logo-link:hover {
  outline: none;
  -webkit-tap-highlight-color: transparent;
  text-decoration: none;
  background-color: transparent;
}

.logo-link img {
  -webkit-user-select: none;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}

.main-content {
  padding: 0 2rem;
  max-width: 100%;
  margin: 0 auto;
}
</style>
