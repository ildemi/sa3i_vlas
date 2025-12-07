import axios from 'axios';
import { useAuthStore } from './stores/auth';  // Asegúrate de importar el store

export const configureAxios = () => {
  // Configuración base de Axios
  axios.defaults.baseURL = import.meta.env.VITE_DJANGO_URL; // || "http://localhost:8002/api/";  // URL base para la API
  axios.defaults.headers['Content-Type'] = 'application/json';  // Encabezado predeterminado

  // Interceptor de respuesta (cuando se recibe una respuesta de la API)
  axios.interceptors.response.use(
    (response) => response,  // Si la respuesta es exitosa, solo devolverla
    async (error) => {
      const originalRequest = error.config;
      const authStore = useAuthStore();  // Obtener el store de autenticación

      // Si la respuesta tiene un error 401 (token expirado o inválido)
      if (error.response && error.response.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        const refresh_token = localStorage.getItem('refreshToken');  // Obtén el refresh token
        if (refresh_token) {
          try {
            // Solicitar un nuevo token de acceso usando el refresh token
            const response = await axios.post(`${import.meta.env.VITE_DJANGO_URL}token/refresh/`, {
              refresh: refresh_token,
            });

            // Guarda el nuevo access token en localStorage
            localStorage.setItem('token', response.data.access);

            // Reintentar la solicitud original con el nuevo access token
            originalRequest.headers['Authorization'] = `Bearer ${response.data.access}`;
            return axios(originalRequest);  // Reintentar la solicitud original con el nuevo token
          } catch (err) {
            console.error('Error al refrescar el token:', err);
            authStore.logout();  // Llamamos al logout si no se pudo refrescar el token
          }
        } else {
          authStore.logout();  // Si no hay refresh token, hacemos logout
        }
      }

      return Promise.reject(error);  // Si no es un error 401, rechazar la promesa
    }
  );
};
