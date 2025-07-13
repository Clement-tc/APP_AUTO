FROM python:3.11-slim

# Port exposé par Flask
EXPOSE 5000

# Installer quelques dépendances système utiles (notamment pour fitz / matplotlib)
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libpq-dev \
    build-essential \
    python3-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Définir le dossier de travail
WORKDIR /app

# Copier les dépendances et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source (app.py + modules + modèles)
COPY . .

# Lancer l'application Flask
CMD ["python", "app.py"]
