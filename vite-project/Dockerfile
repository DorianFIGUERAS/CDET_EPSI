# Stage 1: Build stage
FROM node:22-bookworm-slim AS build

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of your source code
COPY . .

# Build the application (output usually goes to /app/dist)
RUN npm run build

# Stage 2: Production stage
FROM nginx:alpine-slim

# Copy custom nginx config if you have one (optional)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the static build files from the build stage to the nginx html folder
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]