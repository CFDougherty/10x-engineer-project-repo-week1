# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# API key — passed from docker-compose as a build arg so the frontend and
# backend share a single API_KEY value in the root .env file.
ARG API_KEY=""
ENV VITE_API_KEY=$API_KEY

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source files
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# apache2-utils provides htpasswd for HTTP Basic Auth password generation
RUN apk add --no-cache apache2-utils

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Entrypoint generates the nginx config at startup so auth_basic is
# enabled only when API_KEY is provided at runtime.
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]