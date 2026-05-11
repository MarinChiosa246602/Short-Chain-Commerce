# Multi-stage build: build React app, then serve with nginx
FROM node:18-alpine AS builder

WORKDIR /app

# Copy web app files
COPY web/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source and build
COPY web/ ./
RUN npm run build

# Production stage: serve with nginx
FROM nginx:alpine

# Copy nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Copy built React app from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
