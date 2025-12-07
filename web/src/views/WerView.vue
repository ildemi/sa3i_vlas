<template>
  <div class="container my-4">
    <h2 class="text-center mb-4">Word Error Rate (WER) & Accuracy</h2>

    <div v-if="loading" class="text-center my-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Calculating metrics...</p>
    </div>

    <div v-else-if="error" class="alert alert-danger text-center">
      {{ error }}
    </div>

    <div v-else-if="wer === null" class="alert alert-info text-center">
      No audios found to compute the WER.
    </div>

    <div v-else class="metrics text-center">
      <p class="metric-label">Word Error Rate (WER)</p>
      <p class="metric-value">{{ (wer * 100).toFixed(2) }}%</p>

      <p class="metric-label">Estimated Accuracy</p>
      <p class="metric-value">{{ (100 - wer * 100).toFixed(2) }}%</p>

      <p class="note">
        Accuracy is calculated as <code>100% - WER</code>.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import type { AxiosError } from 'axios'

const wer = ref<number | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const fetchWER = async () => {
  loading.value = true
  error.value = null
  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL
    const response = await axios.get(`${djangourl}wer/`)
    wer.value = response.data.global_average_wer
  } catch (err: unknown) {
    const axiosError = err as AxiosError
    if (axiosError.response?.status === 400 && typeof axiosError.response.data === 'object') {
      const data = axiosError.response.data as { detail?: string }
      error.value = data.detail ?? 'Unable to compute WER.'
    } else {
      error.value = 'An unexpected error occurred while retrieving WER.'
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchWER()
})
</script>

<style scoped>
.container {
  width: 95%;
  max-width: 1200px;
  margin: 2rem auto;
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #2c3e50;
}

h2 {
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

.alert {
  margin-top: 20px;
}

.metrics {
  margin-top: 2rem;
}

.metric-label {
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 0.2rem;
  color: #1976d2;
}

.metric-value {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  color: #0d47a1;
  font-family: 'Courier New', Courier, monospace;
}

.note {
  font-size: 0.9rem;
  color: #555;
  font-style: italic;
}
</style>
