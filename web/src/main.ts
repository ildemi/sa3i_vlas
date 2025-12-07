import './assets/main.css'

// Importa Bootstrap CSS
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'
import 'bootstrap-icons/font/bootstrap-icons.css'

// Importa Vue Toastification
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

import { configureAxios } from './axiosInstance';  // Importa la función para configurar Axios

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.use(Toast, {
  timeout: 3000, // Duración del popup en milisegundos
  position: 'top-right', // Posición del popup
})

// Configura Axios (añade interceptores)
configureAxios();

app.mount('#app')

console.log('VITE_DJANGO_URL =', import.meta.env.VITE_DJANGO_URL);

