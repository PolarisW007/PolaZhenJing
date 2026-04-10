# =============================================================================
# Module: Dockerfile (Frontend)
# Description: Docker image for React+Vite dev server
# Created: 2026-04-06
# Author: PolaZhenjing Team
# =============================================================================

FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
