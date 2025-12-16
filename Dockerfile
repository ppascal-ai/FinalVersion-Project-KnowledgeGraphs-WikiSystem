# Dockerfile

FROM python:3.11-slim

WORKDIR /code

# Installer les dépendances système minimales si besoin (optionnel pour l'instant)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential && \
#     rm -rf /var/lib/apt/lists/*

# Copier les requirements et les installer
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code
COPY . .

# Commande par défaut (surchargée par docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
