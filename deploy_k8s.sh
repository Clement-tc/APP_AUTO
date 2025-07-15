#!/bin/bash

set -e

# === PARAMÈTRES ===
NAMESPACE="offreapi"
BASE_IMAGE_NAME="offre-api"
TAG="v1-$(date +%s)"
IMAGE_NAME="$BASE_IMAGE_NAME:$TAG"
DEPLOYMENT_FILE_ORIG="k8s/deployment.yaml"
DEPLOYMENT_FILE_TMP="k8s/deployment.tmp.yaml"

echo "🕓 Nouveau tag généré : $TAG"

# === CONFIGURATION MINIKUBE (facultatif) ===
echo "🧠 Configuration de Minikube (RAM/CPU)..."
minikube config set memory 8250
minikube config set cpus 4

# === DÉMARRAGE DOCKER ET MINIKUBE ===
echo "🐳 Démarrage de Docker Desktop (si nécessaire)..."
open -a Docker || true
sleep 5

echo "🚀 Démarrage de Minikube..."
minikube start

# === CONTEXTE DOCKER PAR DÉFAUT ===
docker context use default > /dev/null

# === BUILD & PUSH IMAGE ===
echo "🔨 Build image Docker : $IMAGE_NAME"
eval $(minikube docker-env)
docker build -t "$IMAGE_NAME" .

# === CLEAN NAMESPACE & RECRÉATION ===
echo "🔥 Nettoyage namespace $NAMESPACE..."
kubectl delete namespace $NAMESPACE --wait=true || true
kubectl create namespace $NAMESPACE

# === DÉPLOIEMENT DE LA BASE + SECRETS ===
echo "📦 Déploiement PostgreSQL + Secret..."
kubectl apply -f k8s/secret.yaml -n $NAMESPACE
kubectl apply -f k8s/postgres-config.yaml -n $NAMESPACE
kubectl apply -f k8s/postgres-deployment.yaml -n $NAMESPACE
kubectl apply -f k8s/postgres-service.yaml -n $NAMESPACE

# === ATTENTE DE POSTGRES ===
echo "⏳ Attente de readiness Postgres..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=90s

# === MODIFICATION TEMPORAIRE DU DEPLOYMENT (nouveau tag) ===
cp "$DEPLOYMENT_FILE_ORIG" "$DEPLOYMENT_FILE_TMP"
sed -i '' "s|image: .*$|image: $IMAGE_NAME|g" "$DEPLOYMENT_FILE_TMP"

# === DÉPLOIEMENT DE L'API & PGADMIN ===
echo "🚀 Déploiement de l'API & pgAdmin..."
kubectl apply -f "$DEPLOYMENT_FILE_TMP" -n $NAMESPACE
kubectl apply -f k8s/pgadmin-deployment.yaml -n $NAMESPACE
rm "$DEPLOYMENT_FILE_TMP"

# === RÉSULTAT FINAL ===
echo -e "\n✅ Déploiement terminé dans le namespace : $NAMESPACE"
kubectl get pods -n $NAMESPACE
