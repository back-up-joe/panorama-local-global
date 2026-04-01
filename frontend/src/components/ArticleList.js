// src/components/ArticleList.js (versión actualizada)
import React, { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { articleService } from "../services/api";
import visitService from "../services/visitService";
import Footer from "./Footer";

const ArticleList = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterCategory, setFilterCategory] = useState("");
  const [totalArticles, setTotalArticles] = useState(0);
  const [totalVisits, setTotalVisits] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");

  // Estados para paginación
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize] = useState(9);
  
  // Obtener parámetros de búsqueda de la URL
  const [searchParams] = useSearchParams();

  useEffect(() => {
    // Obtener término de búsqueda de la URL
    const searchFromUrl = searchParams.get('search');
    if (searchFromUrl) {
      setSearchTerm(searchFromUrl);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchArticles();
    registerAndGetVisits();
  }, [currentPage, searchTerm]); // Añadir searchTerm como dependencia

  // Escuchar eventos de búsqueda personalizados
  useEffect(() => {
    const handleSearchEvent = (event) => {
      setSearchTerm(event.detail);
      setCurrentPage(1); // Resetear a primera página cuando se busca
    };
    
    window.addEventListener('search', handleSearchEvent);
    
    return () => {
      window.removeEventListener('search', handleSearchEvent);
    };
  }, []);

  // En ArticleList.js, modifica la función fetchArticles
const fetchArticles = async () => {
  try {
    setLoading(true);
    setError(null);

    console.log(`Iniciando fetchArticles para página ${currentPage}...`);
    console.log(`Término de búsqueda: "${searchTerm}"`);
    
    // Pasa searchTerm a la función getArticles
    const data = await articleService.getArticles(currentPage, pageSize, searchTerm);
    console.log("Data recibida:", data);

    if (data && data.results && Array.isArray(data.results)) {
      console.log(
        `Recibidos ${data.results.length} artículos de ${data.count} totales`
      );
      setArticles(data.results);
      setTotalArticles(data.count);
      
      const pages = Math.ceil(data.count / pageSize);
      setTotalPages(pages);
      
      console.log(`Página ${currentPage} de ${pages}`);
    } else if (Array.isArray(data)) {
      console.log(`Recibidos ${data.length} artículos`);
      setArticles(data);
      setTotalArticles(data.length);
      setTotalPages(1);
    } else {
      console.error("Formato de datos inesperado:", data);
      setError("Formato de datos incorrecto recibido de la API");
    }
  } catch (err) {
    console.error("Error en fetchArticles:", err);
    const errorMsg = err.message || "Error desconocido";
    const status = err.response?.status || "N/A";
    setError(`Error ${status}: ${errorMsg}`);
  } finally {
    setLoading(false);
  }
};

  const handlePageChange = (pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setCurrentPage(pageNumber);
    }
  };

  const registerAndGetVisits = async () => {
    console.log("Registrando visita...");
    const visits = await visitService.registerVisit();
    console.log("Visitas obtenidas:", visits);
    setTotalVisits(visits);
  };  

  const categories =
    articles.length > 0
      ? [
          ...new Set(
            articles.map((article) => article.category).filter(Boolean)
          ),
        ]
      : [];

  const filteredArticles = filterCategory
    ? articles.filter((article) => article.category === filterCategory)
    : articles;

  const Pagination = () => {
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    const pages = [];
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    return (
      <nav aria-label="Navegación de páginas">
        <ul className="pagination justify-content-center">
          <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
            <button 
              className="page-link" 
              onClick={() => handlePageChange(1)}
              disabled={currentPage === 1}
            >
              &laquo;
            </button>
          </li>
          <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
            <button 
              className="page-link" 
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              &lsaquo;
            </button>
          </li>
          
          {startPage > 1 && (
            <li className="page-item disabled">
              <span className="page-link">...</span>
            </li>
          )}
          
          {pages.map(page => (
            <li key={page} className={`page-item ${currentPage === page ? 'active' : ''}`}>
              <button 
                className="page-link" 
                onClick={() => handlePageChange(page)}
              >
                {page}
              </button>
            </li>
          ))}
          
          {endPage < totalPages && (
            <li className="page-item disabled">
              <span className="page-link">...</span>
            </li>
          )}
          
          <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
            <button 
              className="page-link" 
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              &rsaquo;
            </button>
          </li>
          <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
            <button 
              className="page-link" 
              onClick={() => handlePageChange(totalPages)}
              disabled={currentPage === totalPages}
            >
              &raquo;
            </button>
          </li>
        </ul>
      </nav>
    );
  };

  if (loading) {
    return (
      <div className="text-center my-5">
        <div className="spinner-border text-danger" role="status">
          <span className="visually-hidden">Cargando...</span>
        </div>
        <p className="mt-2">Cargando noticias...</p>
        <small className="text-muted">
          Conectando a servidor
        </small>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container my-5">
        <div className="alert alert-danger" role="alert">
          <h4 className="alert-heading">Error al cargar artículos</h4>
          <p>{error}</p>

          <div className="mt-3">
            <button className="btn btn-danger me-2" onClick={fetchArticles}>
              Reintentar
            </button>
            <a href="/" className="btn btn-outline-dark">
              Recargar página
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="container">
        {/* Header con filtro de categorías */}
        <div className="d-flex justify-content-between align-items-center mb-4">
          <h2 className="mb-0">Portal de noticias</h2>
          
          {/* CONTADOR DE VISITAS */}
          <div className="badge bg-danger ps-3 pe-3 py-2 fs-6">
            {totalVisits.toLocaleString()} visitas
          </div>     
        </div>
        <hr></hr>
        <div>
          <p><i>Información para despertar, análisis para entender, herramientas para actuar.</i></p>
        </div>
        <hr></hr>

        {/* Mostrar término de búsqueda activo */}
        {searchTerm && (
        <div 
          className="alert alert-dismissible fade show mb-4" 
          style={{
            backgroundColor: '#fff0f0',
            borderColor: '#f6c5c5',
            borderWidth: '2px',
            borderStyle: 'solid',
            color: '#721c24'
        }}
        >
        <i className="bi bi-search me-2" style={{ color: '#dc3545' }}></i>
        Resultados para: <strong style={{ color: '#dc3545' }}>"{searchTerm}"</strong>
        <button 
          type="button" 
          className="btn-close" 
          onClick={() => {
            setSearchTerm('');
            setCurrentPage(1);
            window.dispatchEvent(new CustomEvent('search', { detail: '' }));
          }}
          style={{ filter: 'brightness(0.8)' }}
        ></button>
        </div>
      )}

        {/* Lista de artículos */}
        {filteredArticles.length === 0 ? (
          <div className="alert alert-warning">
            {articles.length === 0
              ? searchTerm 
                ? `No se encontraron artículos que coincidan con "${searchTerm}"`
                : "No hay artículos disponibles"
              : `No hay artículos en la categoría "${filterCategory}"`}
            {(filterCategory || searchTerm) && (
              <button
                className="btn btn-sm btn-warning ms-3"
                onClick={() => {
                  setFilterCategory("");
                  setSearchTerm("");
                  setCurrentPage(1);
                  window.dispatchEvent(new CustomEvent('search', { detail: '' }));
                }}
              >
                {filterCategory ? "Ver todas" : "Limpiar búsqueda"}
              </button>
            )}
          </div>
        ) : (
          <>
            <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
              {filteredArticles.map((article) => (
                <div className="col" key={article.id}>
                  <div className="card h-100 shadow-sm hover-shadow">
                    {/* Imagen del artículo */}
                    {article.image_url ? (
                      <img
                        src={article.image_url}
                        className="card-img-top"
                        alt={article.title}
                        style={{
                          height: "200px",
                          objectFit: "cover",
                          width: "100%",
                        }}
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = "";
                        }}
                      />
                    ) : (
                      <div
                        className="card-img-top bg-secondary d-flex align-items-center justify-content-center"
                        style={{ height: "200px" }}
                      >
                        <span className="text-white">Sin imagen</span>
                      </div>
                    )}

                    <div className="card-body d-flex flex-column">
                      {/* Categoría */}
                      {article.category && (
                        <div className="mb-2">
                          <span className="badge bg-danger">
                            {article.category}
                          </span>
                        </div>
                      )}

                      {/* Título */}
                      <h5
                        className="card-title"
                        style={{
                          minHeight: "auto",
                          lineHeight: "1.4",
                          marginBottom: "0.75rem",
                        }}
                      >
                        {article.title}
                      </h5>

                      {/* Subtítulo */}
                      <p
                        className="card-text text-muted"
                        style={{
                          minHeight: "auto",
                          lineHeight: "1.5",
                          marginBottom: "1rem",
                        }}
                      >
                        {article.subtitle && article.subtitle.length > 200
                          ? `${article.subtitle.substring(0, 200)}...`
                          : article.subtitle}
                      </p>

                      <div className="mt-auto">
                        {/* Información de fecha y autor */}
                        <div className="d-flex justify-content-between align-items-center mb-2">
                          <small className="text-muted">
                            <i className="bi bi-calendar me-1"></i>
                            {article.publication_date}
                          </small>
                          <small className="text-muted">
                            <i className="bi bi-person me-1"></i>
                            {article.author || "Anónimo"}
                          </small>
                        </div>

                        {/* Botón para ver detalles */}
                        <Link
                          to={`/article/${article.slug}`}
                          className="btn btn-danger w-100"
                        >
                          <i className="bi bi-eye me-1"></i>
                          Leer artículo
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Paginación */}
            {totalPages > 1 && (
              <div className="mt-4">
                <Pagination />
              </div>
            )}

            {/* Información del total */}
            <div className="mt-4 text-center">
              <div className="alert alert-light border">
                <p className="mb-0">
                  <strong>{articles.length}</strong> artículos de <strong>{totalArticles}</strong>
                  {filterCategory && ` en categoría "${filterCategory}"`}
                  <br />
                  <small className="text-muted">
                    Página {currentPage} de {totalPages}
                  </small>
                </p>
              </div>
            </div>
          </>
        )}
      </div>  
      <Footer/>
    </>   
  );
};

export default ArticleList;