import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { articleService } from '../services/api';

import Footer from './Footer';

const ArticleDetail = () => {
  const { id } = useParams();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchArticle();
  }, [id]);

  const fetchArticle = async () => {
    try {
      setLoading(true);
      const data = await articleService.getArticleDetail(id);
      setArticle(data);
    } catch (err) {
      setError('Error al cargar el artículo. Por favor, intente nuevamente.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center my-5">
        <div className="spinner-border text-danger" role="status">
          <span className="visually-hidden">Cargando...</span>
        </div>
        <p className="mt-2">Cargando artículo...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger" role="alert">
        {error}
        <div className="mt-3">
          <Link to="/" className="btn btn-outline-danger">
            Volver al inicio
          </Link>
        </div>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="alert alert-warning" role="alert">
        Artículo no encontrado.
        <div className="mt-3">
          <Link to="/" className="btn btn-outline-danger">
            Volver al inicio
          </Link>
        </div>
      </div>
    );
  }

  return (
    <>
    <div className="container my-4">
      {/* Botón volver */}
      <div className="mb-4">
        <Link to="/" className="btn btn-outline-dark">
          Volver a noticias
        </Link>
      </div>

      {/* Encabezado del artículo */}
      <div className="mb-5">
        {article.category && (
          <span className="badge bg-danger mb-3 fs-6">
            {article.category}
          </span>
        )}
        <h1 className="display-5 fw-bold mb-3">{article.title}</h1>
        <p className="lead text-muted mb-4">{article.subtitle}</p>
        
        <div className="d-flex flex-wrap gap-3 mb-4">
          <div className="text-muted">
            <i className="bi bi-calendar me-1"></i>
            {article.publication_date}
          </div>
          <div className="text-muted">
            <i className="bi bi-person me-1"></i>
            {article.author || 'Anónimo'}
          </div>
        </div>
      </div>

      {/* Imagen principal */}
      {article.image_url && (
        <div className="mb-5 text-center">
          <img
            src={article.image_url}
            className="img-fluid rounded shadow"
            alt={article.title}
            style={{ maxHeight: '500px', width: 'auto', maxWidth: '100%' }}
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = '';
            }}
          />
          <p className="text-muted mt-2 small">
            {article.title}
          </p>
        </div>
      )}

      {/* Contenido del artículo */}
      <div className="mb-5">
        <h3 className="mb-4">Contenido</h3>
        <div className="article-content fs-5" style={{ lineHeight: '1.8' }}>
          {article.content && article.content.split('\n').map((paragraph, index) => (
            <p key={index} className="mb-4">
              {paragraph}
            </p>
          ))}
        </div>
      </div>

      {/* Información adicional */}
      <div className="card bg-light mb-5">
        <div className="card-body">
          <h5 className="card-title mb-4">
            <i className="bi bi-info-circle me-2"></i>
            Información del artículo
          </h5>
          <div className="row">
            <div className="col-md-6">
              <ul className="list-unstyled">
                <li className="mb-2">
                  <strong>Categoría:</strong> {article.category || 'No especificada'}
                </li>
                <li className="mb-2">
                  <strong>Autor:</strong> {article.author || 'No especificado'}
                </li>                                
              </ul>
            </div>
            <div className="col-md-6">
              <ul className="list-unstyled">
                <li className="mb-2">
                  <strong>Fecha de publicación:</strong> {article.publication_date}
                </li>
                {article.url && (
                  <li className="mb-2">
                    <strong>URL original:</strong>
                    <a 
                      href={article.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="ms-2 small"
                    >
                      Ver noticia
                    </a>
                  </li>
                )}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Botones de navegación */}
      <div className="d-flex justify-content-between mb-5">
        <Link to="/" className="btn btn-outline-danger">
          Volver a todas las noticias
        </Link>
        <button
          className="btn btn-outline-dark ms-3"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        >
          Volver arriba
        </button>
      </div>
    </div>
    <Footer />
    </>
  );
};

export default ArticleDetail;