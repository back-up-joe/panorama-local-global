#FROM node:18-alpine AS builder

#WORKDIR /app

#COPY . .

#RUN npm install

# Build the app
#RUN npm run build

# Install serve and run
#RUN npm install -g serve

#EXPOSE 3000

#CMD ["serve", "-s", "build", "-l", "3000"]

###############################################################################

FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Build the app
RUN npm run build

FROM node:18-alpine AS production
WORKDIR /app

COPY --from=builder /app/build ./build

# Install serve and run
RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"]



