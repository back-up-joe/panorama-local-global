#!/bin/bash

# Cargar variables de entorno desde el archivo .env si existe
if [ -f /app/.env ]; then
    export $(grep -v '^#' /app/.env | xargs)
fi

# Cargar variables de entorno del contenedor
export $(cat /proc/1/environ | tr '\0' '\n' | xargs)

# Configurar Django
export DJANGO_SETTINGS_MODULE=scraper.settings
export PYTHONUNBUFFERED=1

# Cambiar al directorio de la app
cd /app

# Ejecutar el script
/usr/local/bin/python /app/scripts/scrap_elsiglo.py