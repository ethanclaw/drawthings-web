FROM node:18-slim

WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY server.js ./
COPY public/ ./public/
COPY config/ ./config/

EXPOSE 3002

CMD ["node", "server.js"]
