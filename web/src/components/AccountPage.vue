<template>
  <div class="account-container">
    <h1>My Account</h1>
    <div class="account-info" v-if="userData">
      <div class="info-group">
        <label>Username:</label>
        <p>{{ userData.username }}</p>
      </div>
      <div class="info-group">
        <label>First name:</label>
        <p>{{ userData.first_name }}</p>
      </div>
      <div class="info-group">
        <label>Last Name:</label>
        <p>{{ userData.last_name }}</p>
      </div>
      <div class="info-group">
        <label>Email:</label>
        <p>{{ userData.email }}</p>
      </div>
      <div class="info-group">
        <label>Last Login:</label>
        <p>{{ userData.lastLogin }}</p>
      </div>
    </div>
    <div v-else class="text-center my-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Loading account information...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()

const userData = ref<{ username: string, first_name: string, last_name: string, email: string, lastLogin: string } | null>(null)

onMounted(async () => {
  const token = localStorage.getItem('token')

  if (!token) {
    router.push('/login')
    return
  }

  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL;
    const response = await axios.get(djangourl + 'profile/', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    userData.value = { ...response.data }
  } catch (error) {
    console.error('Error fetching user data:', error)
    router.push('/login')
  }
})
</script>

<style scoped>
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
  margin-bottom: 2rem;
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
  grid-template-columns: 120px 1fr;
  align-items: center;
  padding: 1.2rem;
  background: #f8f9fa;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.info-group:hover {
  transform: translateX(5px);
  background: #f0f4f8;
}

label {
  font-weight: 600;
  color: #2196f3;
  text-transform: uppercase;
  font-size: 0.9rem;
  letter-spacing: 0.5px;
}

p {
  margin: 0;
  color: #333;
  font-size: 1rem;
}

.button-group {
  display: flex;
  gap: 10px;
}

.btn {
  align-self: flex-start;
}
</style>
