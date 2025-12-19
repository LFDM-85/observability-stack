FROM python:3.11-slim

WORKDIR /app

# Instala dependências
RUN pip install --no-cache-dir flask requests

# Copia o script
COPY teams-webhook-adapter.py .

# Expõe a porta
EXPOSE 8080

# Comando para executar
CMD ["python", "teams-webhook-adapter.py"]