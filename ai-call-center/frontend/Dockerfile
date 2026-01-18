# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM node:20-alpine AS runner

WORKDIR /app

# Install serve globally
RUN npm install -g serve

# Copy built files from builder
COPY --from=builder /app/dist ./dist

# Set environment variable
ENV PORT=3000

# Create start script
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'serve -s dist -l ${PORT:-3000}' >> /start.sh && \
    chmod +x /start.sh

# Expose port
EXPOSE 3000

# Start the app
CMD ["/start.sh"]
