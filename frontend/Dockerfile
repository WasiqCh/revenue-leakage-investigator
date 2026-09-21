# TICKET-002 owns this file.
FROM node:22-slim

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

# Plain-English: install dependencies from the lockfile so every developer and
# CI gets the same tree. package.json is copied first so Docker can reuse the
# layer when only source files change.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
