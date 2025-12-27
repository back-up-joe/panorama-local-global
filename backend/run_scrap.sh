#!/bin/bash
cd /app
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi
export DB_HOST=${DB_HOST:-db}
echo "[$(date)] Ejecutando scraping..." >> /var/log/cron.log
usr/local/bin/python3 /app/scripts/scrap_elsiglo.py >> /var/log/cron.log 2>&1
