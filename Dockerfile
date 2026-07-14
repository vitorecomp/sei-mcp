# Use official Node.js Alpine image for minimal footprint
FROM node:22-alpine AS build

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code and build
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

# Production runtime stage
FROM node:22-alpine AS production

WORKDIR /app

# Copy built artifacts and production dependencies
COPY package*.json ./
RUN npm ci --only=production

COPY --from=build /app/dist ./dist

# Environment settings
ENV PORT=3000
ENV HOST=0.0.0.0
ENV NODE_ENV=production

EXPOSE 3000

CMD ["node", "dist/server.js"]
