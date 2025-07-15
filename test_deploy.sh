#!/bin/bash
minikube start 


eval $(minikube docker-env)
docker build -t offre-api:latest .
docker images | grep offre-api
kubectl create namespace offreapi || true

kubectl apply -f k8s/
kubectl get pods -n offreapi




