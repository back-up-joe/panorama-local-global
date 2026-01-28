import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-danger text-white mt-5 border-top">
      <div className="container py-5">
        <div className="row justify-content-center">

          {/* Texto */}
          <div className="col-12 text-center mb-4">
            <small>
              © {currentYear} | Resistencia Informativa
            </small>
          </div>

          {/* Formulario */}
          <div className="col-12 col-md-10 col-lg-8 mt-4">
            <form
              action="https://formspree.io/f/meekopoy"
              method="POST"
              className="bg-danger text-white p-4 rounded shadow border border-light"
            >
              <h5 className="mb-4 text-center fw-bold">
                Contacto
              </h5>

              <div className="mb-3">
                <label className="form-label">Email</label>
                <input
                  type="email"
                  name="email"
                  className="form-control bg-white"
                  placeholder=""
                  required
                />
              </div>

              <div className="mb-3">
                <label className="form-label">Mensaje</label>
                <textarea
                  name="message"
                  className="form-control bg-white"
                  rows="4"
                  placeholder=""
                  required
                />
              </div>

              <div className="text-end">
                <button
                  type="submit"
                  className="btn btn-outline-light"
                >
                  Enviar mensaje
                </button>
              </div>
            </form>
          </div>

        </div>
      </div>
    </footer>
  );
};

export default Footer;
