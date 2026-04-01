import React from 'react';
import { Link } from 'react-router-dom';
import SearchBar from './SearchBar';

const Navbar = () => {
  return (
    <>
      <nav className="navbar navbar-expand-lg navbar-dark bg-danger shadow">
        <div className="container">
          <Link className="navbar-brand" to="/">
            Resistencia Informativa
          </Link>
        </div>
      </nav>
      <SearchBar />
    </>
  );
};

export default Navbar;