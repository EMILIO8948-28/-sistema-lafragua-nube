FROM node:22-slim
WORKDIR /app
COPY package.json servidor.js ./
COPY publico ./publico
COPY precarga ./precarga
ENV LF_MODO=nube
ENV DATA_DIR=/data
EXPOSE 10000
CMD ["node", "servidor.js"]
