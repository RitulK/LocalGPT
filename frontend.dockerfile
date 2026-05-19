# Frontend Dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source code
COPY frontend/ .

# Expose frontend port
EXPOSE 5173

# Run Vite dev server (for development)
# For production, use: RUN npm run build && CMD ["npm", "run", "preview"]
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
