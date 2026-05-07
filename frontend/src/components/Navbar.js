import React from 'react';
import { Link } from 'react-router-dom';
import SearchBar from './SearchBar';

const Navbar = () => {
  return (
    <>
      <nav className="navbar navbar-expand-lg navbar-dark bg-danger shadow">
        <div className="container">
          <Link className="navbar-brand" to="/">
            RESISTENCIA INFORMATIVA
          </Link>

          {/* Solo ícono de Instagram */}
          <a 
            href="https://www.instagram.com/resistencia_informativa_org/" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-white ms-auto"
            style={{ fontSize: '1.5rem' }}
          >
            <i className="fab fa-instagram"></i>
          </a>
        </div>
      </nav>
      <SearchBar />
    </>
  );
};

export default Navbar;