# Usar uma imagem base do Python
FROM python:3.9-slim

# Instalar dependências
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Definir o diretório de trabalho
WORKDIR /app

# Copiar o código do servidor para o container
COPY . .

# Instalar dependências do Python
RUN pip install flask

# Expor a porta do servidor
EXPOSE 5000

# Definir o diretório padrão para gravações
ENV OUTPUT_DIR=/var/www/recordings

# Criar o diretório de gravações
RUN mkdir -p ${OUTPUT_DIR}

# Comando para rodar o servidor
CMD ["python", "server.py"]
