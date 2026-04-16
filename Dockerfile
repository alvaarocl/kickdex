# Usar imagen base de Python oficial
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias de sistema para soccerdata y compilación
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requerimientos e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto que usa FastAPI
EXPOSE 8000

# Comando para ejecutar la aplicación usando uvicorn
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
