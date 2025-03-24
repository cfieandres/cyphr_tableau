#!/bin/bash

# Script to deploy the Tableau AI Extension to GitHub Pages

echo "Building React app for GitHub Pages..."
npm run build

echo "Deploying to GitHub Pages..."
npm run deploy

echo "Done! Your app is now deployed to GitHub Pages."
echo "Remember to rebuild and redeploy your backend API server with HTTPS enabled."
echo "Run the following command in your backend directory to rebuild your Docker container:"
echo "docker build -t cyphr-api-server . && docker run -p 8000:8000 -p 443:443 cyphr-api-server"