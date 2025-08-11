#!/bin/bash

echo "🔧 Fixing Docker build issues..."

# Stop all running containers
echo "Stopping all containers..."
docker-compose down

# Remove all containers
echo "Removing all containers..."
docker container prune -f

# Remove all images
echo "Removing all images..."
docker image prune -a -f

# Remove all volumes
echo "Removing all volumes..."
docker volume prune -f

# Remove all networks
echo "Removing all networks..."
docker network prune -f

# Clear Docker build cache
echo "Clearing Docker build cache..."
docker builder prune -a -f

# Clean npm cache in frontend directory
echo "Cleaning npm cache..."
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
cd ..

# Rebuild with no cache
echo "Rebuilding with no cache..."
docker-compose build --no-cache

echo "✅ Docker cleanup complete! You can now run: docker-compose up"