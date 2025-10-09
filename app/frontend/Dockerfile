# Dockerfile for MEDSECUREX frontend (Next.js)
FROM node:20-alpine AS builder
WORKDIR /app
COPY . .
RUN npm install --legacy-peer-deps
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app .
EXPOSE 3000
CMD ["npm", "run", "start"]
