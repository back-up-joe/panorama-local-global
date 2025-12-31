FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    ca-certificates \
    cron \
    postgresql-client \
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

# Variables de entorno por defecto para Celery y Django
ENV DJANGO_SETTINGS_MODULE=scraper.settings
ENV PYTHONUNBUFFERED=1
ENV CELERY_BROKER_URL=redis://redis:6379/0
ENV CELERY_RESULT_BACKEND=redis://redis:6379/1

EXPOSE 8000

# CMD ["gunicorn", "scraper.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-"]
