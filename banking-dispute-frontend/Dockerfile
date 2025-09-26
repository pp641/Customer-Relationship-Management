FROM node:20-alpine
WORKDIR /app

# Copy and install
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build with env var
ARG VITE_REACT_APP_API_URL
ENV VITE_REACT_APP_API_URL=$VITE_REACT_APP_API_URL
RUN npm run build
