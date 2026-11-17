FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
# Optional Grafana Faro collector URL, baked into the bundle at build time.
ARG VITE_FARO_URL
ENV VITE_FARO_URL=$VITE_FARO_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
