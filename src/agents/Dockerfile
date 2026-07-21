FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de agentes
COPY main.py .
COPY spec_agent/ ./spec_agent/
COPY impl_agent/ ./impl_agent/
COPY review_agent/ ./review_agent/
COPY eval_agent/ ./eval_agent/
COPY shared/ ./shared/

# Exponer puerto FastAPI
EXPOSE 8000

# Comando para ejecutar (asume que hay un main.py o similar)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
