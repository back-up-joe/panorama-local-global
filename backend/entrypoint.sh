#!/bin/bash
set -e

echo "=== INICIANDO BACKEND ==="
echo "Hora: $(date)"
echo ""

# 1. Crear el script run_scrap.sh si no existe
if [ ! -f /app/run_scrap.sh ]; then
    echo "Creando script run_scrap.sh..."
    cat > /app/run_scrap.sh << 'EOF'
#!/bin/bash

# Este script se ejecuta CADA MINUTO vía cron
cd /app

# Cargar variables de entorno
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Asegurar variables críticas
export DB_HOST=${DB_HOST:-db}
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-scraper.settings}

echo "[$(date)] Iniciando scraping..." >> /var/log/scrap.log
/usr/local/bin/python3 /app/scripts/scrap_elsiglo.py >> /var/log/scrap.log 2>&1
echo "[$(date)] Scraping completado" >> /var/log/scrap.log
EOF
    chmod +x /app/run_scrap.sh
fi

# 2. Configurar cron job CORRECTAMENTE
echo "Configurando cron job..."
# FORMATO CORRECTO para /etc/cron.d/: 
# m h dom mon dow user command
# * * * * * root /app/run_scrap.sh >> /var/log/cron.log 2>&1
# Pero mejor usar crontab directamente:

echo "* * * * * /app/run_scrap.sh >> /var/log/cron.log 2>&1" > /etc/cron.d/scrap-cron
# NOTA: En /etc/cron.d/ NO se incluye el campo "user" si es para root
chmod 0644 /etc/cron.d/scrap-cron

# O mejor aún, usar crontab directamente:
echo "* * * * * /app/run_scrap.sh >> /var/log/cron.log 2>&1" | crontab -

# 3. Iniciar cron
echo "Iniciando cron service..."
cron

# 4. Crear y configurar archivos de log
echo "Configurando logs..."
touch /var/log/cron.log /var/log/scrap.log
chmod 666 /var/log/cron.log /var/log/scrap.log

# 5. Dar permisos al script (por si acaso)
chmod +x /app/run_scrap.sh

# 6. Verificar que el script existe
echo "Verificando scripts..."
ls -la /app/run_scrap.sh
ls -la /app/scripts/scrap_elsiglo.py

# 7. Ejecutar migraciones
echo "Ejecutando migraciones de Django..."
python manage.py makemigrations
python manage.py migrate

# 8. Colectar archivos estáticos
echo "Colectando archivos estáticos..."
python manage.py collectstatic --noinput

# 9. Mostrar configuración de cron
echo "Configuración de cron actual:"
crontab -l
echo ""

# 10. Iniciar Gunicorn
echo "Iniciando Gunicorn..."
echo "=== BACKEND INICIADO ==="
exec gunicorn scraper.wsgi:application --bind 0.0.0.0:8000 --access-logfile -