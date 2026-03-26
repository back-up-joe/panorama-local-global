import React, { useState, useEffect } from 'react';
import { commentService } from '../services/api';

const CommentSection = ({ articleId }) => {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    comment: ''
  });
  const [formErrors, setFormErrors] = useState({});
  const [submitSuccess, setSubmitSuccess] = useState(false);

  useEffect(() => {
    fetchComments();
  }, [articleId]);

  const fetchComments = async () => {
    try {
      setLoading(true);
      const data = await commentService.getComments(articleId);
      setComments(data);
    } catch (err) {
      setError('Error al cargar los comentarios');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const validateForm = () => {
    const errors = {};
    
    if (!formData.name.trim()) {
      errors.name = 'El nombre es obligatorio';
    } else if (formData.name.length < 2) {
      errors.name = 'El nombre debe tener al menos 2 caracteres';
    }
    
    if (!formData.email.trim()) {
      errors.email = 'El email es obligatorio';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Ingresa un email válido';
    }
    
    if (!formData.comment.trim()) {
      errors.comment = 'El comentario es obligatorio';
    } else if (formData.comment.length < 5) {
      errors.comment = 'El comentario debe tener al menos 5 caracteres';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Limpiar error del campo cuando el usuario empieza a escribir
    if (formErrors[name]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    try {
      setSubmitting(true);
      const newComment = await commentService.addComment(articleId, formData);
      setComments(prev => [newComment, ...prev]);
      setSubmitSuccess(true);
      setFormData({ name: '', email: '', comment: '' });
      setFormErrors({});
      
      // Ocultar mensaje de éxito después de 3 segundos
      setTimeout(() => {
        setSubmitSuccess(false);
      }, 3000);
    } catch (err) {
      console.error('Error al enviar comentario:', err);
      setError(err.response?.data?.message || 'Error al enviar el comentario. Por favor, intenta nuevamente.');
      setTimeout(() => setError(null), 5000);
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading && comments.length === 0) {
    return (
      <div className="text-center my-4">
        <div className="spinner-border text-danger spinner-border-sm" role="status">
          <span className="visually-hidden">Cargando comentarios...</span>
        </div>
        <p className="text-muted mt-2 small">Cargando comentarios...</p>
      </div>
    );
  }

  return (
    <div className="comments-section mb-5">
      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white py-3 border-bottom">
          <h4 className="mb-0">
            <i className="bi bi-chat-dots me-2"></i>
            Comentarios ({comments.length})
          </h4>
        </div>
        
        <div className="card-body">
          {/* Formulario para nuevo comentario */}
          <div className="mb-4">
            <h5 className="mb-3">Deja tu comentario</h5>
            
            {submitSuccess && (
              <div className="alert alert-success alert-dismissible fade show" role="alert">
                <i className="bi bi-check-circle me-2"></i>
                ¡Comentario enviado exitosamente!
                <button 
                  type="button" 
                  className="btn-close" 
                  onClick={() => setSubmitSuccess(false)}
                ></button>
              </div>
            )}
            
            {error && (
              <div className="alert alert-danger" role="alert">
                <i className="bi bi-exclamation-triangle me-2"></i>
                {error}
              </div>
            )}
            
            <form onSubmit={handleSubmit}>
              <div className="row">
                <div className="col-md-6 mb-3">
                  <label htmlFor="name" className="form-label">
                    Nombre <span className="text-danger">*</span>
                  </label>
                  <input
                    type="text"
                    className={`form-control ${formErrors.name ? 'is-invalid' : ''}`}
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    placeholder="Tu nombre"
                  />
                  {formErrors.name && (
                    <div className="invalid-feedback">{formErrors.name}</div>
                  )}
                </div>
                
                <div className="col-md-6 mb-3">
                  <label htmlFor="email" className="form-label">
                    Email <span className="text-danger">*</span>
                  </label>
                  <input
                    type="email"
                    className={`form-control ${formErrors.email ? 'is-invalid' : ''}`}
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder="tu@email.com"
                  />
                  {formErrors.email && (
                    <div className="invalid-feedback">{formErrors.email}</div>
                  )}
                  <div className="form-text text-muted small">
                    <i className="bi bi-info-circle me-1"></i>
                    Tu email no será publicado.
                  </div>
                </div>
              </div>
              
              <div className="mb-3">
                <label htmlFor="comment" className="form-label">
                  Comentario <span className="text-danger">*</span>
                </label>
                <textarea
                  className={`form-control ${formErrors.comment ? 'is-invalid' : ''}`}
                  id="comment"
                  name="comment"
                  rows="4"
                  value={formData.comment}
                  onChange={handleInputChange}
                  placeholder="Escribe tu comentario aquí..."
                ></textarea>
                {formErrors.comment && (
                  <div className="invalid-feedback">{formErrors.comment}</div>
                )}
              </div>
              
              <button
                type="submit"
                className="btn btn-danger"
                disabled={submitting}
              >
                {submitting ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Enviando...
                  </>
                ) : (
                  <>
                    <i className="bi bi-send me-2"></i>
                    Publicar comentario
                  </>
                )}
              </button>
            </form>
          </div>
          
          <hr className="my-4" />
          
          {/* Lista de comentarios existentes */}
          <div className="comments-list">
            <h5 className="mb-3">
              <i className="bi bi-chat-square-text me-2"></i>
              Comentarios recientes
            </h5>
            
            {comments.length === 0 ? (
              <div className="text-center py-5 text-muted bg-light rounded">
                <i className="bi bi-chat-square-text fs-1"></i>
                <p className="mt-3 mb-0">No hay comentarios aún.</p>
                <p className="small">¡Sé el primero en comentar!</p>
              </div>
            ) : (
              comments.map((comment) => (
                <div key={comment.id} className="comment-item mb-4 pb-3 border-bottom">
                  <div className="d-flex justify-content-between align-items-start mb-2">
                    <div>
                      <strong className="text-danger">
                        <i className="bi bi-person-circle me-1"></i>
                        {comment.name}
                      </strong>
                      <span className="text-muted ms-2 small">
                        <i className="bi bi-calendar3 me-1"></i>
                        {comment.formatted_date || formatDate(comment.created_at)}
                      </span>
                    </div>
                  </div>
                  <div className="comment-content ps-3">
                    <p className="mb-0" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>
                      {comment.comment}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommentSection;