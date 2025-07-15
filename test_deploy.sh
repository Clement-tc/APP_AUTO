#!/bin/bash
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

kubectl apply -f k8s/
kubectl get pods -n offreapi




