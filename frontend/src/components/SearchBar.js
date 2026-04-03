// src/components/SearchBar.js
import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const SearchBar = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      if (location.pathname === '/') {
        window.dispatchEvent(new CustomEvent('search', { detail: searchTerm }));
      } else {
        navigate(`/?search=${encodeURIComponent(searchTerm)}`);
      }
    }
  };

  const handleClear = () => {
    setSearchTerm('');
    if (location.pathname === '/') {
      window.dispatchEvent(new CustomEvent('search', { detail: '' }));
    } else {
      navigate('/');
    }
  };

  return (
    <div className="search-bar-container bg-dark py-3">
      <div className="container">
        <div className="row justify-content-end">
          <div className="col-md-6 col-lg-5 col-xl-4">
            <form onSubmit={handleSubmit} className="search-form">
              <div className="input-group">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Buscar por título..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  style={{
                    fontSize: '1rem',
                    border: '1px solid #ced4da',
                    borderRadius: '8px 0 0 8px',
                    borderRight: 'none',
                    padding: '0.5rem 0.75rem',
                    height: '48px'
                  }}
                />
                {searchTerm && (
                  <button
                    type="button"
                    className="btn btn-outline-secondary"
                    onClick={handleClear}
                    style={{
                      border: '1px solid #ced4da',
                      borderLeft: 'none',
                      borderRight: 'none',
                      backgroundColor: 'white',
                      padding: '0.5rem 0.75rem',
                      height: '48px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    <i className="bi bi-x-lg" style={{ fontSize: '0.875rem' }}></i>
                  </button>
                )}
                <button
                  type="submit"
                  className="btn btn-danger"
                  style={{
                    borderRadius: '0 8px 8px 0',
                    paddingLeft: '20px',
                    paddingRight: '20px',
                    fontSize: '1rem',
                    height: '48px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <i className="bi bi-search" style={{ fontSize: '0.875rem' }}></i>
                  Buscar
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <style jsx>{`
        .search-bar-container {
          background-color: #000000;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .form-control:focus {
          box-shadow: none;
          border-color: #ced4da;
          outline: none;
        }
        .btn-outline-secondary {
          border-color: #ced4da;
          color: #6c757d;
        }
        .btn-outline-secondary:hover {
          background-color: #f8f9fa;
          border-color: #ced4da;
          color: #6c757d;
        }
        .btn-outline-secondary:focus {
          box-shadow: none;
        }
        .form-control::placeholder {
          font-size: 1rem;
        }
        @media (max-width: 768px) {
          .col-md-6 {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
};

export default SearchBar;