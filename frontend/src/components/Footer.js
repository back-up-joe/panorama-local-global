import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-danger text-white text-center p-5 mt-5 border-top">
      <small>
        © {currentYear} | Resistencia Informativa | Todos los derechos reservados.
      </small>
    </footer>
  );
};

export default Footer;
