import axios from 'axios';

// Configura la URL base de API Django
const API_BASE_URL = 'http://localhost:8000/api/';

// const API_BASE_URL = 'http://159.203.81.186:8000/api/';

// const API_BASE_URL = process.env.REACT_APP_API_URL;

console.log('API_BASE_URL desde .env:', API_BASE_URL);  // Añade esta línea

const api = axios.create({
// const apiBackend = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

export const articleService = {
  // Obtener lista de artículos
  getArticles: async () => {
    try {
      console.log('Haciendo petición a:', `${API_BASE_URL}/articles/`);
      const response = await api.get('articles/');
      // const response = await apiBackend.get('articles/');
      console.log('API Response STATUS:', response.status);
      console.log('API Response HEADERS:', response.headers);
      
      return response.data;
    } catch (error) {      
      console.error('Error COMPLETO fetching articles:');

      throw error;
    }
  },

  // Obtener detalle de un artículo
  getArticleDetail: async (id) => {
    try {
      const response = await api.get(`/articles/${id}/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching article ${id}:`, error);
      throw error;
    }
  }
};

export default api;
