# Utiliser Python 3.12 comme image de base
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires pour Linux
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Mettre à jour pip
RUN pip install --no-cache-dir --upgrade pip

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python une par une pour mieux gérer les conflits
RUN pip install --no-cache-dir numpy==1.26.4 && \
    pip install --no-cache-dir opencv-python==4.10.0.84 && \
    pip install --no-cache-dir dlib==19.24.6 && \
    pip install --no-cache-dir face-recognition==1.3.0 && \
    pip install --no-cache-dir face_recognition_models==0.3.0 && \
    pip install --no-cache-dir websockets==13.1 && \
    pip install --no-cache-dir Pillow==10.4.0 && \
    pip install --no-cache-dir python-dotenv==1.0.1 && \
    pip install --no-cache-dir requests==2.32.3 && \
    pip install --no-cache-dir PyJWT==2.8.0 && \
    pip install --no-cache-dir supabase==2.9.1 && \
    pip install --no-cache-dir tensorflow==2.17.0 && \
    pip install --no-cache-dir mtcnn==0.1.1 && \
    pip install --no-cache-dir easydict==1.10 && \
    pip install --no-cache-dir tqdm==4.67.0 && \
    pip install --no-cache-dir torch==2.7.0 && \
    pip install --no-cache-dir torchvision==0.22.0 && \
    pip install --no-cache-dir tensorboardX==2.5.1

# Copier le reste des fichiers du projet
COPY . .

# Exposer le port pour le websocket
EXPOSE 8765

# Commande pour démarrer le serveur websocket
CMD ["python", "websocket_server.py"] 