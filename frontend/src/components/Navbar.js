import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-danger shadow">
      <div className="container">
        <Link className="navbar-brand" to="/">
          Resistencia Informativa
        </Link>
      </div>
    </nav>
  );
};

export default Navbar;