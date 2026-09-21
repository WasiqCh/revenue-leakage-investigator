# Minimal scaffold. TICKET-001 owns the final version of this file.
FROM node:22-slim

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
