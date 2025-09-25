FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files first (for caching)
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy all source code (includes tsconfig.json, src/, public/)
COPY . .

# Build the app
RUN npm run build

# Runtime env injection for dynamic API_URL
CMD envsubst < /app/public/config.js > /app/public/config.generated.js && \
    mv /app/public/config.generated.js /app/public/config.js && \
    npm run preview -- --host 0.0.0.0 --port 4173
