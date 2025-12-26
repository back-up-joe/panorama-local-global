#!/bin/bash
# Arrancar cron en background
cron -f &

# Arrancar gunicorn en foreground
exec gunicorn scraper.wsgi:application --bind 0.0.0.0:8000
