FROM node:18-alpine AS builder

WORKDIR /app

COPY . .
# COPY package.json . 

# First, check what's in package.json (for debugging)
# RUN echo "Checking package.json..." && cat package.json | grep -A5 -B5 "scripts"

RUN npm install

# Verify react-scripts is installed
# RUN ls -la node_modules/.bin/ | grep react-scripts || echo "react-scripts not found!"

# Copy source code
# COPY . .

# Build the app
RUN npm run build

# Install serve and run
RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"]
