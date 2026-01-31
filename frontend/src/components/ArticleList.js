import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { articleService } from "../services/api";

import Footer from "./Footer";

const ArticleList = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterCategory, setFilterCategory] = useState("");
  const [totalArticles, setTotalArticles] = useState(0);

  useEffect(() => {
    fetchArticles();
  }, []);

  const fetchArticles = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log("Iniciando fetchArticles...");
      const data = await articleService.getArticles();
      console.log("Data recibida:", data);

      // La API devuelve un objeto con paginación
      // La propiedad "results" contiene los artículos
      if (data && data.results && Array.isArray(data.results)) {
        console.log(
          `Recibidos ${data.results.length} artículos de ${data.count} totales`
        );
        setArticles(data.results);
        setTotalArticles(data.count || data.results.length);
      } else if (Array.isArray(data)) {
        // Por si acaso en algún momento devuelve array directo
        console.log(`Recibidos ${data.length} artículos`);
        setArticles(data);
        setTotalArticles(data.length);
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

  // Extraer categorías únicas de los artículos
  const categories =
    articles.length > 0
      ? [
          ...new Set(
            articles.map((article) => article.category).filter(Boolean)
          ),
        ]
      : [];

  // Filtrar artículos por categoría
  const filteredArticles = filterCategory
    ? articles.filter((article) => article.category === filterCategory)
    : articles;

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
        <div className="d-flex align-items-center gap-3">
          <span className="badge bg-danger ps-2 pe-2">
            {filteredArticles.length} artículos
          </span>
        </div>        
      </div>
      <hr></hr>
      <div>
        {/*
        <p>Aquí se comparten noticias nacionales e internacionales traídas desde diversos portales informativos. Queremos contribuir a la difusión de artículos y análisis que los medios de comunicación hegemónicos no profundizan. Estas noticias son obtenidas mediante el método de web scraping y esperamos ir ampliando la cantidad y diversidad de nuestras fuentes. No tenemos fines de lucro y agradecemos la difusión.</p>
        */}
        <p><i>"Información para despertar, análisis para entender, herramientas para actuar"</i> (Noam Chomsky).</p>
      </div>
      <hr></hr>

      {/* Lista de artículos - MOSTRANDO TODOS */}
      {filteredArticles.length === 0 ? (
        <div className="alert alert-warning">
          {articles.length === 0
            ? "No hay artículos disponibles"
            : `No hay artículos en la categoría "${filterCategory}"`}
          {filterCategory && (
            <button
              className="btn btn-sm btn-warning ms-3"
              onClick={() => setFilterCategory("")}
            >
              Ver todas
            </button>
          )}
        </div>
      ) : (
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
                      e.target.src =
                        "";
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

                  {/* Título - SIN CORTE, altura automática */}
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

                  {/* Subtítulo - con límite de caracteres */}
                  <p
                    className="card-text text-muted"
                    style={{
                      minHeight: "auto",
                      lineHeight: "1.5",
                      marginBottom: "1rem",
                    }}
                  >
                    {article.subtitle.length > 200
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
                      to={`/article/${article.id}`}
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
      )}

      {/* Información del total */}
      {filteredArticles.length > 0 && (
        <div className="mt-4 text-center">
          <div className="alert alert-light border">
            <p className="mb-0">
              Mostrando <strong>{articles.length}</strong> artículos
            </p>
          </div>
        </div>
      )}      
    </div>  
    <Footer/>
  </>   
  );
};

export default ArticleList;
