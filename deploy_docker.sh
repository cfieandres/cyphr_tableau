#!/bin/bash

# Simple deployment script for cyphr AI Extension Docker setup

# Ensure we have a .env file
if [ ! -f .env ]; then
  echo "Creating .env file from sample..."
  cp .env.sample .env
  echo "Please edit .env file with your credentials before continuing."
  exit 1
fi

# Build and start containers
echo "Building and starting containers..."
docker-compose up --build -d

# Check if containers are running
echo "Checking container status..."
docker-compose ps

echo ""
echo "Deployment completed!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo ""
echo "To view logs, run: docker-compose logs -f"
echo "To stop containers, run: docker-compose down"