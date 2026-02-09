import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add request interceptor for logging (development only)
if (process.env.NODE_ENV === 'development') {
  api.interceptors.request.use(
    (config) => {
      console.log(`[API] ${config.method.toUpperCase()} ${config.url}`);
      return config;
    },
    (error) => {
      console.error('[API Error]', error);
      return Promise.reject(error);
    }
  );
}

// SWR fetcher function
export const fetcher = (url) => api.get(url).then(res => res.data);

// Export axios instance for custom requests
export default api;
