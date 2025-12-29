#!/bin/bash

# Script para ejecutar el comando Django
cd /app
/usr/local/bin/python /app/scripts/scrap_elsiglo.py 2>&1 | tee -a /var/log/cron.log

# Dale permisos de ejecución
chmod +x /cron.sh