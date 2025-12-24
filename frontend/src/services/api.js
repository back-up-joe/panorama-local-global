import axios from 'axios';

// Configura la URL base de tu API Django
const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
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
      const response = await api.get('/articles/');
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