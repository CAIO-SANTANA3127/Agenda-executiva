# ================================================
# evolution-api/Dockerfile (DENTRO DA PASTA evolution-api)
# ================================================
FROM node:18-alpine

# Instalar dependências do sistema
RUN apk add --no-cache curl git

# Diretório de trabalho
WORKDIR /evolution

# Copiar package.json primeiro (para cache do Docker)
COPY package*.json ./

# Instalar dependências
RUN npm install

# Copiar todo o código
COPY . .

# Compilar TypeScript
RUN npm run build

# Criar diretórios necessários
RUN mkdir -p /evolution/instances /evolution/db

# Expor porta
EXPOSE 8080

# Comando para iniciar
CMD ["npm", "start"]