FROM node:18-alpine AS builder

WORKDIR /app

# Copiamos solo lo necesario para instalar dependencias ######
#COPY package*.json ./
#RUN npm install
################################################

COPY . .

RUN npm install

# Build the app
RUN npm run build

# Etapa 2: producción FROM node:18-alpine AS production WORKDIR /app
#FROM node:18-alpine AS production
#######################################################

# Copiamos solo la carpeta build desde la etapa anterior
#COPY --from=builder /app/build ./build

# Install serve and run
RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"]
