import axios from 'axios';

// Configura la URL base de API Django desde las variables de entorno
const API_BASE_URL = process.env.REACT_APP_API_URL;

console.log('API_BASE_URL desde .env:', API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

export const articleService = {
  // Obtener lista de artículos con paginación y búsqueda
  getArticles: async (page = 1, pageSize = 15, search = '') => {
    try {
      console.log(`Haciendo petición a: ${API_BASE_URL}/articles/?page=${page}&page_size=${pageSize}`);
      if (search) {
        console.log(`Con término de búsqueda: "${search}"`);
      }
      
      // Construir los parámetros
      const params = {
        page: page,
        page_size: pageSize
      };
      
      // Agregar parámetro de búsqueda si existe
      if (search && search.trim()) {
        params.search = search.trim();
      }
      
      const response = await api.get('articles/', { params });
      
      console.log('API Response STATUS:', response.status);
      console.log('API Response DATA:', response.data);
      
      return response.data;
    } catch (error) {      
      console.error('Error COMPLETO fetching articles:', error);
      if (error.response) {
        console.error('Error response data:', error.response.data);
        console.error('Error response status:', error.response.status);
      }
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

// Servicio específico para comentarios
export const commentService = {
  // Obtener comentarios de un artículo
  getComments: async (articleId) => {
    try {
      const response = await api.get(`/articles/${articleId}/comments/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching comments for article ${articleId}:`, error);
      throw error;
    }
  },
  
  // Agregar un comentario
  addComment: async (articleId, commentData) => {
    try {
      const response = await api.post(`/articles/${articleId}/add-comment/`, commentData);
      return response.data;
    } catch (error) {
      console.error(`Error adding comment to article ${articleId}:`, error);
      throw error;
    }
  },
  
  // Obtener cantidad de comentarios
  getCommentsCount: async (articleId) => {
    try {
      const response = await api.get(`/articles/${articleId}/comments-count/`);
      return response.data.comments_count;
    } catch (error) {
      console.error(`Error fetching comments count for article ${articleId}:`, error);
      throw error;
    }
  }
};

export default api;