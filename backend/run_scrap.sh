#!/bin/bash
cd /app

# Load .env file if it exists
#if [ -f .env ]; then
#    export $(grep -v '^#' .env | xargs)
#fi

if [ -f .env ]; then
    # Use source/dot command to load the file
    set -a  # Automatically export all variables
    source .env
    set +a
fi

export DB_HOST=${DB_HOST:-db}

# Debug logging
echo "[$(date)] Environment check:"  
echo "[$(date)] DB_HOST: $DB_HOST" >> /var/log/cron.log
echo "[$(date)] DB_USER: $DB_USER" >> /var/log/cron.log
echo "[$(date)] DB_NAME: $DB_NAME" >> /var/log/cron.log
echo "[$(date)] PWD: $(pwd)"

echo "[$(date)] Ejecutando scraping..." >> /var/log/cron.log
/usr/local/bin/python3 /app/scripts/scrap_elsiglo.py >> /var/log/cron.log 2>&1
