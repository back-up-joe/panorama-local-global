#!/usr/bin/env bash
set -e

# Arranca el deamon de cron en segundo plano
#exec /usr/sbin/cron -f &

cron

# Proceso principal: arranca el servidor Gunicorn
exec gunicorn scraper.wsgi:application --bind 0.0.0.0:8000
