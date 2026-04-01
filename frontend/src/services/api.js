// src/services/api.js

import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const articleService = {
  // Obtener lista de artículos con paginación y búsqueda
  getArticles: async (page = 1, pageSize = 9, search = '') => {
    try {
      let url = `/articles/?page=${page}&page_size=${pageSize}`;
      if (search && search.trim()) {
        url += `&search=${encodeURIComponent(search.trim())}`;
      }
      const response = await api.get(url);
      return response.data;
    } catch (error) {
      console.error('Error fetching articles:', error);
      throw error;
    }
  },

  // Obtener detalle de artículo por slug
  getArticleDetail: async (slug) => {
    try {
      const response = await api.get(`/articles/${slug}/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching article detail:', error);
      throw error;
    }
  },

  // Método de compatibilidad para obtener por ID (si es necesario)
  getArticleById: async (id) => {
    try {
      const response = await api.get(`/articles/by-id/${id}/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching article by id:', error);
      throw error;
    }
  },

  // Obtener comentarios de un artículo
  getArticleComments: async (slug) => {
    try {
      const response = await api.get(`/articles/${slug}/comments/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching comments:', error);
      throw error;
    }
  },

  // Agregar comentario a un artículo
  addComment: async (slug, commentData) => {
    try {
      const response = await api.post(`/articles/${slug}/add-comment/`, commentData);
      return response.data;
    } catch (error) {
      console.error('Error adding comment:', error);
      throw error;
    }
  },

  // Obtener contador de comentarios
  getCommentsCount: async (slug) => {
    try {
      const response = await api.get(`/articles/${slug}/comments-count/`);
      return response.data.comments_count;
    } catch (error) {
      console.error('Error fetching comments count:', error);
      return 0;
    }
  },
};

// NUEVO: Servicio específico para comentarios
export const commentService = {
  // Obtener comentarios de un artículo
  getComments: async (articleId) => {
    try {
      // Si articleId es numérico, asumimos que es ID; si no, es slug
      const isNumeric = /^\d+$/.test(articleId);
      let endpoint;
      
      if (isNumeric) {
        // Si es ID numérico, usar el endpoint de compatibilidad
        endpoint = `/articles/by-id/${articleId}/comments/`;
      } else {
        // Si es slug, usar el endpoint normal
        endpoint = `/articles/${articleId}/comments/`;
      }
      
      const response = await api.get(endpoint);
      return response.data;
    } catch (error) {
      console.error('Error fetching comments:', error);
      throw error;
    }
  },

  // Agregar comentario a un artículo
  addComment: async (articleId, commentData) => {
    try {
      const isNumeric = /^\d+$/.test(articleId);
      let endpoint;
      
      if (isNumeric) {
        endpoint = `/articles/by-id/${articleId}/add-comment/`;
      } else {
        endpoint = `/articles/${articleId}/add-comment/`;
      }
      
      const response = await api.post(endpoint, commentData);
      return response.data;
    } catch (error) {
      console.error('Error adding comment:', error);
      throw error;
    }
  },

  // Obtener contador de comentarios
  getCommentsCount: async (articleId) => {
    try {
      const isNumeric = /^\d+$/.test(articleId);
      let endpoint;
      
      if (isNumeric) {
        endpoint = `/articles/by-id/${articleId}/comments-count/`;
      } else {
        endpoint = `/articles/${articleId}/comments-count/`;
      }
      
      const response = await api.get(endpoint);
      return response.data.comments_count;
    } catch (error) {
      console.error('Error fetching comments count:', error);
      return 0;
    }
  },

  // Obtener comentarios pendientes (solo admin)
  getPendingComments: async () => {
    try {
      const response = await api.get('/articles/comments/pending/');
      return response.data;
    } catch (error) {
      console.error('Error fetching pending comments:', error);
      throw error;
    }
  },

  // Aprobar un comentario (solo admin)
  approveComment: async (articleId, commentId) => {
    try {
      const isNumeric = /^\d+$/.test(articleId);
      let endpoint;
      
      if (isNumeric) {
        endpoint = `/articles/by-id/${articleId}/comments/${commentId}/approve/`;
      } else {
        endpoint = `/articles/${articleId}/comments/${commentId}/approve/`;
      }
      
      const response = await api.patch(endpoint);
      return response.data;
    } catch (error) {
      console.error('Error approving comment:', error);
      throw error;
    }
  },

  // Eliminar un comentario (solo admin)
  deleteComment: async (articleId, commentId) => {
    try {
      const isNumeric = /^\d+$/.test(articleId);
      let endpoint;
      
      if (isNumeric) {
        endpoint = `/articles/by-id/${articleId}/comments/${commentId}/delete/`;
      } else {
        endpoint = `/articles/${articleId}/comments/${commentId}/delete/`;
      }
      
      const response = await api.delete(endpoint);
      return response.data;
    } catch (error) {
      console.error('Error deleting comment:', error);
      throw error;
    }
  },
};

export default api;