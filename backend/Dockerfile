FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt update && apt upgrade -y \
    && rm -rf /var/lib/apt/lists/*

##############################################################

#RUN apt-get update && \
 #   curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-linux-keyring.gpg && \
  #  echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
   # apt-get update && apt-get install -y google-chrome-stable && \
    #rm -rf /var/lib/apt/lists/*

#RUN google-chrome --headless --no-sandbox --disable-gpu --remote-debugging-port=9222 --disable-dev-shm-usage &

###############################################################

# 2. Instalar Google Chrome (versión estable)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    # Instalar ChromeDriver (importante para Selenium)
    && wget -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/121.0.6167.85/linux64/chromedriver-linux64.zip \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    # Limpieza
    && rm -rf /var/lib/apt/lists/* /tmp/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicación
COPY . .

# Crear usuario no-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Comando por defecto
CMD ["gunicorn", "scraper.wsgi:application", "--bind", "0.0.0.0:8000"]
