# Dockerfile for MEDSECUREX frontend (Next.js)
FROM node:20-alpine AS builder
WORKDIR /app

# Copy package files first for better caching
COPY app/frontend/package*.json ./
RUN npm install --legacy-peer-deps

# Copy the rest of the frontend application
COPY app/frontend/ .

# Set production environment
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV production

# Build the application
RUN npm run build


FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Copy only necessary files for standalone Next.js
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./

EXPOSE 3000

CMD ["node", "server.js"]
