FROM python:3.11-slim

# Installer dépendances système nécessaires
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

# Copier tout le code de l'app
COPY . .

# Exposer le port de Flask/Gunicorn
EXPOSE 5000

# Lancer avec Gunicorn (wsgi:app = fichier wsgi.py, variable app)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]