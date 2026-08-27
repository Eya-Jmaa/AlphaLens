# Frontend Dockerfile - multi-stage: build the Vite app, then serve the static
# bundle with nginx. The client's default API base (http://localhost:8000)
# matches docker-compose's backend port mapping, so no build-time API URL is
# needed for the compose stack; override with --build-arg VITE_API_BASE_URL=...
# for a different deployment target.
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
