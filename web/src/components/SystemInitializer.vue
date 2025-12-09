<script setup lang="ts">
import { ref, watch, onUnmounted, onMounted, computed } from 'vue';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
import { useSystemStore } from '@/stores/system';

const systemStore = useSystemStore();
const authStore = useAuthStore();
const showBar = ref(false);

// Autostart on Auth AND Mount
// Combinamos watcher y onMounted para asegurar que no se nos escapa ningún caso
const checkAndStart = () => {
    // Si hay auth, el store se encarga
    if (authStore.isAuthenticated || localStorage.getItem('token')) {
        systemStore.startInitialization();
    }
}

watch(() => authStore.isAuthenticated, (isAuth) => {
    if (isAuth) systemStore.startInitialization();
}, { immediate: true });

onMounted(() => {
    checkAndStart();
});
</script>

<template>
    <!-- Componente Lógico Invisible (Gestiona el Store) -->
</template>
