<template>
  <div class="account-container">
    <h1>Edit Account</h1>
    <div class="account-info" v-if="userData">
      <div class="info-group">
        <label>Username:</label>
        <input v-model="userData.username" type="text" class="form-control" required/>
      </div>
      <div class="info-group">
        <label>First Name:</label>
        <input v-model="userData.first_name" type="text" class="form-control" required/>
      </div>
      <div class="info-group">
        <label>Last Name:</label>
        <input v-model="userData.last_name" type="text" class="form-control" required/>
      </div>
      <div class="info-group">
        <label>Email:</label>
        <input v-model="userData.email" type="email" class="form-control" required/>
      </div>
      <div class="button-group">
        <button @click="saveChanges" class="btn btn-primary mt-3">Save Changes</button>
        <button @click="discardChanges" class="btn btn-secondary mt-3 ml-2">Discard Changes</button>
      </div>
    </div>
    <div v-else>
      <p>Loading...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import eventBus from '@/eventBus'

const router = useRouter()
const toast = useToast()
const userData = ref<{ username: string, first_name: string, last_name: string, email: string } | null>(null)

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

async function saveChanges() {
  if (userData.value) {
    if (!userData.value.username.trim()) {
      toast.error('Username cannot be empty.')
      return
    }

    if (!userData.value.first_name.trim()) {
      toast.error('First name cannot be empty.')
      return
    }

    if (!userData.value.last_name.trim()) {
      toast.error('Last name cannot be empty.')
      return
    }

    if (!isValidEmail(userData.value.email)) {
      toast.error('Please enter a valid email address.')
      return
    }

    try {
      const token = localStorage.getItem('token')
      if (!token) {
        router.push('/login')
        return
      }

      const djangourl = import.meta.env.VITE_DJANGO_URL;
      await axios.put(djangourl + 'profile/', {
        username: userData.value.username,
        first_name: userData.value.first_name,
        last_name: userData.value.last_name,
        email: userData.value.email
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      toast.success('Changes saved successfully!')
      eventBus.emit('navigate', 'Account')

    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response && error.response.data && error.response.data.detail) {
          toast.error(error.response.data.detail)
        } else {
          toast.error('There was an error saving your changes.')
        }
      } else {
        console.error('Unexpected error:', error)
        toast.error('An unexpected error occurred.')
      }
    }
  }
}

function discardChanges() {
  toast.info('Changes discarded.')
  eventBus.emit('navigate', 'Account')
}

function isValidEmail(email: string): boolean {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}
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
}

label {
  font-weight: 600;
  color: #2196f3;
  text-transform: uppercase;
  font-size: 0.9rem;
  letter-spacing: 0.5px;
}

input {
  padding: 0.8rem 1.2rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: white;
  width: 100%;
}

input:focus {
  border-color: #2196f3;
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.2);
  outline: none;
}

.button-group {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
}

.btn {
  padding: 12px 30px;
  border-radius: 50px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  transition: all 0.3s ease;
  border: none;
  cursor: pointer;
}

.btn-primary {
  background: linear-gradient(45deg, #2196f3, #1976d2);
  color: white;
  box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(33, 150, 243, 0.4);
}

.btn-secondary {
  background: linear-gradient(45deg, #757575, #616161);
  color: white;
  box-shadow: 0 4px 15px rgba(117, 117, 117, 0.3);
}

.btn-secondary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(117, 117, 117, 0.4);
}
</style>
