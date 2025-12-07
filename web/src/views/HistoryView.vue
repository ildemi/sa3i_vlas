<template>
  <div class="container my-4">
    <h2 class="text-center mb-4">Saved Transcription</h2>

    <div v-if="isLoading" class="text-center my-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Loading transcription groups...</p>
    </div>

    <div v-else-if="groups.length === 0" class="alert alert-info text-center">No transcription groups found.</div>

    <table v-else class="table table-striped table-bordered rounded-table">
      <thead class="bg-primary text-white">
        <tr>
          <th>Group</th>
          <th>Status</th>
          <th>Creation Date</th>
          <th>Validation</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="group in sortedGroups" :key="group.id">
          <td>{{ group.group_name }}</td>
          <td>{{ formatStatus(group.status) }}</td>
          <td>{{ formatDate(group.creation_date) }}</td>
          <td class="text-center">
            <button v-if="group.validation_status" 
                @click="goToValidationResults(group.id)" 
                class="btn btn-primary btn-sm">
              View Validation
            </button>
            <span v-else class="text-muted">Not Validated</span>
          </td>
          <td class="text-center">
            <button @click="goToGroupDetail(group.id)" class="btn btn-info btn-sm mr-2">See Details</button>
            <button @click="downloadPDF(group.id)" class="btn btn-success btn-sm mr-2">Download PDF</button>
            <button @click="deleteGroup(group.id)" class="btn btn-danger btn-sm">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useToast } from 'vue-toastification'

interface TranscriptionGroup {
  id: string
  status: string
  creation_date: string
  completion_date: string | null
  user: number
  group_name: string
  validation_status?: string
  validation_date?: string
  validation_score?: number
}

const groups = ref<TranscriptionGroup[]>([])
const isLoading = ref(true)

const router = useRouter()
const toast = useToast()

const sortedGroups = computed(() => {
  return [...groups.value].sort((a, b) => new Date(b.creation_date).getTime() - new Date(a.creation_date).getTime())
})

const pollingInterval = ref<number | null>(null);
const POLLING_DELAY = 10000; // 10 segundos

onMounted(async () => {
  await fetchGroups();
  // Iniciar el polling
  pollingInterval.value = window.setInterval(fetchGroups, POLLING_DELAY);
})

onUnmounted(() => {
  // Limpiar el intervalo cuando el componente se desmonta
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value);
  }
})

async function fetchGroups() {
  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL;
    const response = await axios.get(djangourl + 'transcription-groups/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })
    groups.value = response.data
  } catch (error) {
    console.error('Error fetching transcription groups:', error)
    toast.error('Error fetching transcription groups.')
  } finally {
    isLoading.value = false
  }
}

function formatDate(date: string): string {
  const options: Intl.DateTimeFormatOptions = {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }
  return new Date(date).toLocaleDateString('en-US', options)
}

function formatStatus(status: string): string {
  return status
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function goToGroupDetail(groupId: string) {
  router.push({ name: 'group-detail', params: { groupId } })
}

function goToValidationResults(groupId: string) {
  router.push({ name: 'validation-results', params: { groupId } })
}

async function deleteGroup(groupId: string) {
  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL;
    const response = await axios.delete(`${djangourl}transcription-group/${groupId}/delete/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (response.status === 204) {
      groups.value = groups.value.filter(group => group.id !== groupId);
      toast.success('Group deleted successfully!')
    }
  } catch (error) {
    console.error('Error deleting group:', error);
    toast.error('Error deleting group.')
  }
}

async function downloadPDF(groupId: string) {
  try {
    const djangourl = import.meta.env.VITE_DJANGO_URL;
    const response = await axios({
      url: `${djangourl}transcription-group/${groupId}/download-pdf/`,
      method: 'GET',
      responseType: 'blob',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    const blob = response.data;
    const url = window.URL.createObjectURL(blob);

    // Access the underlying XMLHttpRequest object
    const disposition = response.headers['content-disposition'];
    console.log('Content-Disposition:', response.headers);
    let filename = `transcription_group_${groupId}.pdf`; // Default value

    if (disposition && disposition.indexOf('attachment') !== -1) {
      const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
      const matches = filenameRegex.exec(disposition);
      if (matches != null && matches[1]) {
        filename = matches[1].replace(/['"]/g, '');
      }
    }

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();

    window.URL.revokeObjectURL(url);
    toast.success('PDF downloaded successfully!');
  } catch (error) {
    console.error('Error downloading PDF:', error);
    toast.error('Error downloading PDF.');
  }
}
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
}

.upload-section h2,
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

.table {
  font-size: 0.9rem;
  background-color: #ffffff;
  border-radius: 12px; /* Rounded corners for the table */
  overflow: hidden; /* Ensures rounded corners are applied correctly */
}

.table th, .table td {
  text-align: center;
  vertical-align: middle;
}

.table th {
  background-color: #007bff;
}

.btn-sm {
  margin-right: 10px;
}

.badge {
  padding: 5px 10px;
  border-radius: 30px;
  font-weight: 600;
  font-size: 0.75rem;
}
</style>
