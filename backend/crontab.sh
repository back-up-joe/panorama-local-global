# Ejecuta el script cada minuto
* * * * * /cron.sh >> /var/log/cron.log 2>&1

# Para desarrollo, puedes usar cada 5 minutos:
# */5 * * * * root /cron.sh >> /var/log/cron.log 2>&1