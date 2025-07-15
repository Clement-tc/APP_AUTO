#!/bin/bash
git clone https://github.com/Clement-tc/APP_AUTO 
cd APP_AUTO
docker pull python:3.11-slim
minikube start 
helm repo add kubecost https://kubecost.github.io/cost-analyzer/
helm repo update

kubectl create namespace kubecost

helm install kubecost kubecost/cost-analyzer \
  --namespace kubecost \
  --set kubecostToken="1234567890abcdef" \
  --set global.prometheus.enabled=false \
  --set global.prometheus.fqdn="http://prometheus.monitoring.svc.cluster.local"

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

kubectl create namespace monitoring

helm install kube-prom-stack prometheus-community/kube-prometheus-stack --namespace monitoring


eval $(minikube docker-env)
docker build -t offre-api:latest .
docker images | grep offre-api
kubectl create namespace offreapi || true

kubectl apply -f k8s/secret.yaml -n offreapi
kubectl apply -f k8s/postgres-config.yaml -n offreapi
kubectl apply -f k8s/postgres-deployment.yaml -n offreapi
kubectl apply -f k8s/postgres-service.yaml -n offreapi

kubectl wait --for=condition=ready pod -l app=postgres -n offreapi --timeout=90s || true

kubectl apply -f k8s/pgadmin-deployment.yaml -n offreapi
kubectl apply -f k8s/service-monitoring.yaml -n monitoring

kubectl apply -f k8s/deployment.yaml -n offreapi
kubectl get pods -n offreapi 
