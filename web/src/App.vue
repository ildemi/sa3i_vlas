<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSystemStore } from '@/stores/system'
import axios from 'axios'
import SystemInitializer from '@/components/SystemInitializer.vue'

const router = useRouter()
const route = useRoute()

const authStore = useAuthStore()
const systemStore = useSystemStore()

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

function handleBadgeClick() {
    const status = systemStore.modelStatus;
    const msg = systemStore.statusMessage;
                
    if (status === 'error' || status === 'idle') {
        if (confirm(`Estado: [${status.toUpperCase()}] - ${msg || 'Sin mensaje'}\n\n¿Forzar inicio de conexión ahora?`)) {
            systemStore.startInitialization();
        }
    } else {
        alert(`Estado del Sistema IA:\n[${status.toUpperCase()}]\n\nDetalle: ${msg}`);
    }
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
        
        <!-- IA Status Indicator -->
        <div 
            class="ia-status-badge" 
            :class="systemStore.modelStatus" 
            :title="systemStore.statusMessage"
            @click="handleBadgeClick"
        >
            <span class="status-dot"></span>
            IA Status
        </div>

        <RouterLink to="/account">Account</RouterLink>
        <RouterLink to="/wer">WER</RouterLink>
        <button @click="logout" class="nav-button logout-button">Logout</button>
      </nav>
    </div>
  </header>

  <main class="main-content">
    <RouterView />
  </main>
  
  <SystemInitializer />
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

/* IA Status Styles */
.ia-status-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.8rem;
    border-radius: 20px;
    background-color: #f5f5f5;
    font-size: 0.85rem;
    font-weight: 600;
    color: #666;
    color: #666;
    cursor: pointer;
    transition: all 0.3s ease;
    transition: all 0.3s ease;
    border: 1px solid #e0e0e0;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #95a5a6; /* Idle/Gray */
    box-shadow: 0 0 2px rgba(0,0,0,0.2);
}

/* Estados */
.ia-status-badge.loading .status-dot {
    background-color: #f39c12; /* Orange */
    animation: pulse 1.5s infinite;
}
.ia-status-badge.loading {
    border-color: #f39c12;
    color: #d35400;
}

.ia-status-badge.ready .status-dot {
    background-color: #2ecc71; /* Green */
    box-shadow: 0 0 5px #2ecc71;
}
.ia-status-badge.ready {
    background-color: rgba(46, 204, 113, 0.1);
    border-color: #2ecc71;
    color: #27ae60;
}

.ia-status-badge.error .status-dot {
    background-color: #e74c3c; /* Red */
}
.ia-status-badge.error {
    background-color: rgba(231, 76, 60, 0.1);
    color: #c0392b;
}

@keyframes pulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.2); opacity: 0.7; }
    100% { transform: scale(1); opacity: 1; }
}
</style>
