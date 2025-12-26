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

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN echo "* * * * * /usr/local/bin/python /app/scripts/scrap_elsiglo.py >> /var/log/cron.log 2>&1" > /etc/cron.d/scraper \
    && chmod 0644 /etc/cron.d/scraper \
    && crontab /etc/cron.d/scraper

#RUN echo "* * * * * python scripts/scrap_elsiglo.py >> /var/log/cron.log 2>&1" > /etc/cron.d/scraper \
 #   && chmod 0644 /etc/cron.d/scraper \
  #  && crontab /etc/cron.d/scraper

# Crear usuario no-root
# RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
# USER appuser

# Expose port
EXPOSE 8000

# Comando por defecto
# CMD ["gunicorn", "scraper.wsgi:application", "--bind", "0.0.0.0:8000"]

CMD ["/entrypoint.sh"]

