FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    ca-certificates \
    cron \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* 

# # Agregar keyring de Google
RUN wget -q -O /usr/share/keyrings/google-linux-signing-keyring.gpg \
     https://dl.google.com/linux/linux_signing_key.pub

# Agregar repo de Chrome
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-signing-keyring.gpg] \
     http://dl.google.com/linux/chrome/deb/ stable main" \
     > /etc/apt/sources.list.d/google-chrome.list

# Instalar Google Chrome
RUN apt-get update && apt-get install -y \
     google-chrome-stable \
     --no-install-recommends \
     && rm -rf /var/lib/apt/lists/*

# Instalar ChromeDriver que coincida con la versión de Chrome
RUN set -eux; \
    CHROME_VERSION=$(google-chrome --version | awk '{print $3}'); \
    wget -O /tmp/chromedriver.zip \
      "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip"; \
    unzip /tmp/chromedriver.zip -d /tmp/; \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver; \
    chmod +x /usr/local/bin/chromedriver; \
    rm -rf /tmp/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicación
COPY . .

#COPY entrypoint.sh /entrypoint.sh
#RUN chmod +x /entrypoint.sh

#RUN echo "* * * * * /usr/local/bin/python /app/scripts/scrap_elsiglo.py >> /var/log/cron.log 2>&1" > /etc/cron.d/scraper \
 #   && chmod 0644 /etc/cron.d/scraper \
  #  && crontab /etc/cron.d/scraper

#COPY docker/cron/cronjob /etc/cron.d/cronjob
#RUN chmod 0644 /etc/cron.d/cronjob \
 #   && touch /var/log/cron.log

    #RUN echo "* * * * * python scripts/scrap_elsiglo.py >> /var/log/cron.log 2>&1" > /etc/cron.d/scraper \
 #   && chmod 0644 /etc/cron.d/scraper \
  #  && crontab /etc/cron.d/scraper

# Crear usuario no-root
# RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
# USER appuser

# Crear directorios necesarios
#RUN mkdir -p /app/docker/cron

# Si los archivos están en backend/docker/
#COPY docker/entrypoint.sh /entrypoint.sh
#COPY docker/cron/run_scrap.sh /app/run_scrap.sh

# Dar permisos de ejecución
#RUN chmod +x /entrypoint.sh /app/run_scrap.sh


#######################################################
# Copiar y configurar el script wrapper
#COPY docker/cron/run_scrap.sh /app/run_scrap.sh
#RUN chmod +x /app/run_scrap.sh

# Configurar cron job
#COPY docker/cron/cronjob /etc/cron.d/scrap-cron
#RUN chmod 0644 /etc/cron.d/scrap-cron && \
 #   crontab /etc/cron.d/scrap-cron

# Expose port
#EXPOSE 8000

# Comando por defecto
# CMD ["gunicorn", "scraper.wsgi:application", "--bind", "0.0.0.0:8000"]

#CMD ["/entrypoint.sh"]
#CMD ["/app/run_scrap.sh"]

##############################

#COPY docker/entrypoint.sh /entrypoint.sh
#RUN chmod +x /entrypoint.sh
#ENTRYPOINT ["/entrypoint.sh"]

# Crear run_scrap.sh que usa .env
RUN echo '#!/bin/bash' > /app/run_scrap.sh && \
    echo 'cd /app' >> /app/run_scrap.sh && \
    echo 'if [ -f .env ]; then' >> /app/run_scrap.sh && \
    echo '    export $(grep -v "^#" .env | xargs)' >> /app/run_scrap.sh && \
    echo 'fi' >> /app/run_scrap.sh && \
    echo 'export DB_HOST=${DB_HOST:-db}' >> /app/run_scrap.sh && \
    echo 'echo "[$(date)] Iniciando scraping..." >> /var/log/scrap.log' >> /app/run_scrap.sh && \
    echo '/usr/local/bin/python /app/scripts/scrap_elsiglo.py >> /var/log/scrap.log 2>&1' >> /app/run_scrap.sh && \
    echo 'echo "[$(date)] Scraping completado" >> /var/log/scrap.log' >> /app/run_scrap.sh && \
    chmod +x /app/run_scrap.sh

# Crear el entrypoint.sh directamente en Dockerfile
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo '# Configurar cron' >> /entrypoint.sh && \
    echo 'echo "Configurando cron..."' >> /entrypoint.sh && \
    echo 'echo "* * * * * root /app/run_scrap.sh >> /var/log/cron.log 2>&1" > /etc/cron.d/scrap-cron' >> /entrypoint.sh && \
    echo 'chmod 0644 /etc/cron.d/scrap-cron' >> /entrypoint.sh && \
    echo 'crontab /etc/cron.d/scrap-cron' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo '# Iniciar cron' >> /entrypoint.sh && \
    echo 'echo "Iniciando cron service..."' >> /entrypoint.sh && \
    echo 'cron' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo '# Crear y configurar log file' >> /entrypoint.sh && \
    echo 'touch /var/log/cron.log' >> /entrypoint.sh && \
    echo 'chmod 666 /var/log/cron.log' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo '# Ejecutar migraciones' >> /entrypoint.sh && \
    echo 'echo "Ejecutando migraciones..."' >> /entrypoint.sh && \
    echo 'python manage.py makemigrations' >> /entrypoint.sh && \
    echo 'python manage.py migrate' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo '# Colectar archivos estáticos' >> /entrypoint.sh && \
    echo 'echo "Colectando archivos estáticos..."' >> /entrypoint.sh && \
    echo 'python manage.py collectstatic --noinput' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo '# Iniciar Gunicorn' >> /entrypoint.sh && \
    echo 'echo "Iniciando Gunicorn..."' >> /entrypoint.sh && \
    echo 'exec gunicorn scraper.wsgi:application --bind 0.0.0.0:8000 --access-logfile -' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
