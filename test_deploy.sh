#!/bin/bash

eval $(minikube docker-env)
docker build -t elcer/offre-api:latest .
kubectl rollout restart deployment offre-api -n offreapi
