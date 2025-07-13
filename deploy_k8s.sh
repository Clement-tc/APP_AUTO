#!/bin/bash

set -e  # Stop script on error

# === PARAMÈTRES ===
NAMESPACE="offreapi"
BASE_IMAGE_NAME="elcer/offre-api"
TAG="v1-$(date +%s)"
IMAGE_NAME="$BASE_IMAGE_NAME:$TAG"
DEPLOYMENT_FILE_ORIG="k8s/deployment.yaml"
DEPLOYMENT_FILE_TMP="k8s/deployment.tmp.yaml"

echo "🕓 Nouveau tag généré : $TAG"

# === CONFIGURATION MINIKUBE ===
echo "🧠 Configuration de Minikube..."
minikube config set memory 8250
minikube config set cpus 4

# === DOCKER LOCAL ===
echo "🐳 Démarrage de Docker Desktop si nécessaire..."
open -a Docker || true
sleep 5

# === DÉMARRAGE MINIKUBE ===
echo "🚀 Démarrage de Minikube..."
minikube start

# === CONTEXTE DOCKER LOCAL ===
docker context use default > /dev/null

# === BUILD IMAGE ===
echo "🔨 Build de l'image : $IMAGE_NAME"
docker build -t "$IMAGE_NAME" .

# === PUSH DOCKER HUB ===
echo "☁️ Push sur Docker Hub : $IMAGE_NAME"
docker push "$IMAGE_NAME"

# === SUPPRESSION DU NAMESPACE POUR UN DÉPLOIEMENT PROPRE ===
echo "🔥 Suppression du namespace $NAMESPACE..."
kubectl delete namespace $NAMESPACE --wait=true || true
kubectl create namespace $NAMESPACE

# === APPLY DB & SERVICES D'ABORD ===
echo "📦 Déploiement des dépendances : DB, config, secrets..."
kubectl apply -f k8s/secret.yaml -n $NAMESPACE
kubectl apply -f k8s/postgres-config.yaml -n $NAMESPACE
kubectl apply -f k8s/postgres-deployment.yaml -n $NAMESPACE
kubectl apply -f k8s/postgres-service.yaml -n $NAMESPACE

# === ATTENTE QUE POSTGRES SOIT PRÊT ===
echo "⏳ Attente que postgres soit prêt..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=60s

# === MODIFICATION DU DEPLOYMENT AVEC LE NOUVEAU TAG (sans toucher l’init) ===
cp "$DEPLOYMENT_FILE_ORIG" "$DEPLOYMENT_FILE_TMP"
sed -i '' "/name: offre-api/{n;s|image: .*|image: $IMAGE_NAME|;}" "$DEPLOYMENT_FILE_TMP"

# === DÉPLOIEMENT DE L'API & PGADMIN ===
kubectl apply -f "$DEPLOYMENT_FILE_TMP" -n $NAMESPACE
kubectl apply -f k8s/pgadmin-deployment.yaml -n $NAMESPACE
rm "$DEPLOYMENT_FILE_TMP"

# === DÉPLOIEMENT MONITORING ===
echo "📊 Déploiement Prometheus & Grafana..."
kubectl apply -f monitoring/prometheus-configmap.yaml -n $NAMESPACE
kubectl apply -f monitoring/prometheus-deployment.yaml -n $NAMESPACE
kubectl apply -f monitoring/grafana-deployment.yaml -n $NAMESPACE
kubectl apply -f monitoring/grafana-service.yaml -n $NAMESPACE


# === AFFICHAGE FINAL ===
echo "✅ Déploiement terminé. Pods dans le namespace $NAMESPACE :"
kubectl get pods -n $NAMESPACE
