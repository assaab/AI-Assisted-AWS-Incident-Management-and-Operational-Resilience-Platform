FROM node:22-alpine AS build

WORKDIR /app
COPY apps/console/package*.json ./
RUN npm ci
COPY apps/console ./
ENV VITE_API_URL=http://localhost:8080
RUN npm run build

FROM nginx:1.27-alpine
COPY apps/console/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 3000
