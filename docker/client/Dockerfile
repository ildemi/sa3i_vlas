FROM node:20-alpine AS builder 
WORKDIR /app

# 1) Dependencias
COPY web/package*.json ./
RUN npm install

# 2) Código fuente (incluye .env.* si los tienes)
COPY web/ .

# 3) >>> INYECTA LA VARIABLE AL BUILD <<<
# ARG VITE_DJANGO_URL
# ENV VITE_DJANGO_URL=${VITE_DJANGO_URL}
# Forzamos que Vite la vea en tiempo de build:
# RUN VITE_DJANGO_URL=${VITE_DJANGO_URL} 
RUN npm run build

# Etapa 2: Nginx
FROM nginx:stable-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
