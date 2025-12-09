import { defineStore } from 'pinia';
import { ref } from 'vue';
import axios from 'axios';

export const useSystemStore = defineStore('system', () => {
    const modelStatus = ref<'idle' | 'loading' | 'ready' | 'error'>('idle');
    const statusMessage = ref('');
    const progress = ref(0);

    let pollingInterval: number | null = null;

    function setStatus(status: 'idle' | 'loading' | 'ready' | 'error', message: string = '') {
        modelStatus.value = status;
        statusMessage.value = message;
    }

    async function startInitialization(force = false) {
        // Permitir forzar reinicio aunque esté corriendo
        if (force) {
            console.log("SystemStore: Forced restart requested.");
            if (pollingInterval) {
                clearTimeout(pollingInterval);
                pollingInterval = null;
            }
            // Limpiar ID zombie si estamos forzando
            localStorage.removeItem('init_task_id');
            setStatus('idle', ''); // Reset momentáneo
        }

        if (modelStatus.value === 'ready' && !force) return;
        if (pollingInterval && !force) return; // Ya corriendo

        const apiUrl = import.meta.env.VITE_DJANGO_URL;
        if (!apiUrl) {
            setStatus('error', "Conf Error: VITE_DJANGO_URL");
            return;
        }

        // FEEDBACK VISUAL INMEDIATO
        setStatus('loading', "Conectando...");

        // Recuperar Task ID o pedir uno nuevo
        let taskId = localStorage.getItem('init_task_id');

        if (!taskId) {
            setStatus('loading', "Solicitando arranque...");
            try {
                const response = await axios.post(`${apiUrl}system/initialize/`, {}, {
                    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
                });
                taskId = response.data.task_id;
                if (taskId) localStorage.setItem('init_task_id', taskId);
            } catch (e) {
                console.error(e);
                setStatus('error', "Fallo conexión inicial");
                return;
            }
        }

        if (taskId) {
            checkStatusUntilReady(taskId);
        }
    }

    async function checkStatusUntilReady(taskId: string) {
        const apiUrl = import.meta.env.VITE_DJANGO_URL;
        const POLLING_DELAY = 1500;

        const poll = async () => {
            // Si el status es 'error' (puesto manualmente por usuario o fallo), paramos
            if (modelStatus.value === 'error') {
                pollingInterval = null;
                return;
            }

            try {
                const response = await axios.get(`${apiUrl}system/status/?task_id=${taskId}`, {
                    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
                });
                const data = response.data;

                if (data.status === 'ready') {
                    setStatus('ready', "IA Operativa");
                    pollingInterval = null;
                    return;
                }
                else if (data.status === 'loading') {
                    setStatus('loading', data.message || "Cargando componentes...");
                    pollingInterval = window.setTimeout(poll, POLLING_DELAY);
                }
                else {
                    // Error o Unknown
                    setStatus('loading', "Reiniciando tarea...");
                    localStorage.removeItem('init_task_id');
                    pollingInterval = null;
                    startInitialization(true); // Reintentar forzado
                }

            } catch (error) {
                console.warn("Fallo red:", error);

                // IMPORTANTE: Informar al usuario de que estamos reintentando
                setStatus('loading', "Reintentando conexión...");

                pollingInterval = window.setTimeout(poll, 4000);
            }
        };

        // Arrancar loop
        poll();
    }

    return {
        modelStatus,
        statusMessage,
        progress,
        setStatus,
        startInitialization
    };
});
