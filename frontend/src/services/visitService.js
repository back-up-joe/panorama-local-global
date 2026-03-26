import api from './api';

class VisitService {
  async registerVisit() {
    try {
      // Verificar si ya registramos en esta sesión
      if (sessionStorage.getItem('visit_counted')) {
        const response = await api.get('/visits/');
        return response.data.total_visits;
      }
      
      // Registrar nueva visita
      const response = await api.post('/visits/');
      sessionStorage.setItem('visit_counted', 'true');
      return response.data.total_visits;
    } catch (error) {
      console.error('Error al registrar visita:', error);
      return 0;
    }
  }
  
  async getTotalVisits() {
    try {
      const response = await api.get('/visits/');
      return response.data.total_visits;
    } catch (error) {
      console.error('Error al obtener visitas:', error);
      return 0;
    }
  }
}

export default new VisitService();