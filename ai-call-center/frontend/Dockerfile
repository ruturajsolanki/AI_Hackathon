# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Accept build argument for API URL
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the app (VITE_API_URL will be baked in)
RUN echo "Building with VITE_API_URL=$VITE_API_URL" && npm run build

# Production stage
FROM node:20-alpine AS runner

WORKDIR /app

# Install serve globally
RUN npm install -g serve

# Copy built files from builder
COPY --from=builder /app/dist ./dist

# Expose port 8080 (serve default)
EXPOSE 8080

# Start serve on port 8080
CMD ["serve", "-s", "dist", "-l", "8080"]
