#!/bin/bash
# Setup FastMCP server on Kubernetes connecting to MinIO in Docker

echo "Cleaning up previous FastMCP deployment..."
kubectl delete deployment s3-fastmcp-server
kubectl delete service s3-fastmcp-server
kubectl delete configmap s3-server-config
kubectl delete secret s3-server-secrets 

echo "Building the FastMCPDocker image..."
docker build -t s3-fastmcp-server:latest .


# Deploy to Kubernetes
echo "Deploying FastMCP server to Kubernetes..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Wait for deployment to be ready
echo "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=60s deployment/s3-fastmcp-server || {
  echo "Deployment not ready in time, but continuing..."
}

echo "Deployment complete!"
echo "FastMCP Server available at: http://localhost:30999/sse"
echo "Check logs with: kubectl logs -l app=s3-fastmcp-server"
kubectl get pods -l app=s3-fastmcp-server