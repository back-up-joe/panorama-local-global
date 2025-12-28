#!/bin/bash

# Este script se ejecuta CADA MINUTO vía cron
# Solo hace scraping, NO migraciones

# Configurar PATH para incluir Python
export PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin

# Cargar variables de entorno desde el archivo .env
if [ -f /app/.env ]; then
    echo "[$(date)] Cargando variables de .env..." >> /var/log/scrap.log
    # Cargar solo las variables necesarias, evitando comentarios
    set -a
    source /app/.env
    set +a
else
    echo "[$(date)] ERROR: No se encontró /app/.env" >> /var/log/scrap.log
    exit 1
fi

# Si alguna variable no está definida, usar valores por defecto
export DB_HOST=${DB_HOST:-db}
export DB_NAME=${DB_NAME:-scrap_db}
export DB_USER=${DB_USER:-postgres}
export DB_PASSWORD=${DB_PASSWORD}
export DB_PORT=${DB_PORT:-5432}
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-scraper.settings}

# Para depuración (opcional, puedes comentarlo después)
echo "[$(date)] DB_HOST=$DB_HOST, DB_NAME=$DB_NAME" >> /var/log/scrap_debug.log

echo "[$(date)] Iniciando scraping..." >> /var/log/scrap.log

cd /app

# Solo ejecutar el script de scraping
/usr/local/bin/python3 /app/scripts/scrap_elsiglo.py >> /var/log/scrap.log 2>&1

SCRAP_EXIT_CODE=$?

if [ $SCRAP_EXIT_CODE -eq 0 ]; then
    echo "[$(date)] Scraping completado exitosamente" >> /var/log/scrap.log
else
    echo "[$(date)] ERROR: Scraping falló con código $SCRAP_EXIT_CODE" >> /var/log/scrap.log
fi