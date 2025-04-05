# Usar uma imagem base do Python
FROM python:3.9-slim

# Definir o diretório de trabalho
WORKDIR /app

# Copiar o código do servidor para o container
COPY . .

# Instalar dependências
RUN pip install flask requests

# Expor a porta do servidor
EXPOSE 5001

# Comando para rodar o servidor
CMD ["python", "app.py"]
