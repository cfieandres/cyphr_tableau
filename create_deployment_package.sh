#!/bin/bash

# Create a deployment package for cyphr AI Extension
# This package contains everything needed to deploy the application using pre-built images

# Create package directory
PACKAGE_DIR="cyphr-ai-extension-deploy"
PACKAGE_FILE="cyphr-ai-extension-deploy.zip"

echo "Creating deployment package..."
mkdir -p $PACKAGE_DIR

# Copy required files
cp docker-compose.prod.yml $PACKAGE_DIR/docker-compose.yml
cp .env.sample $PACKAGE_DIR/
cp -r docker/ $PACKAGE_DIR/
cp deploy_production.sh $PACKAGE_DIR/deploy.sh
cp IMAGE_DEPLOYMENT.md $PACKAGE_DIR/README.md

# Create zip archive
echo "Creating zip archive..."
zip -r $PACKAGE_FILE $PACKAGE_DIR

# Clean up
echo "Cleaning up..."
rm -rf $PACKAGE_DIR

echo "Deployment package created: $PACKAGE_FILE"
echo "This package contains everything needed to deploy the cyphr AI Extension using pre-built Docker images."