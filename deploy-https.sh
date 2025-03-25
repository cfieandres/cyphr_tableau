#!/bin/bash

# Script to build and run the API server with HTTPS support

# Set environment variables
export USE_HTTPS=true

# Build the Docker image
echo "Building Docker image with HTTPS support..."
docker build -t cyphr-api-server .

# Run the container with HTTPS enabled
echo "Running API server with HTTPS enabled..."
docker run -p 8000:8000 -p 443:443 -e USE_HTTPS=true cyphr-api-server

echo "API server is running with HTTPS at https://154.53.61.191:8000"