# Build stage
FROM node:18-alpine AS builder

# Install necessary build tools
RUN apk add --no-cache git

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Clear npm cache and install dependencies with better error handling
RUN npm cache clean --force && \
    npm ci --silent --no-audit --no-fund || \
    (echo "npm ci failed, trying npm install..." && npm install --silent --no-audit --no-fund)

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]