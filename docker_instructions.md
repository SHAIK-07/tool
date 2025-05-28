# Docker Instructions for Sunmax Renewables Management System

This document provides step-by-step instructions for building, pushing, and using the Docker image for the Sunmax Renewables Management System.

## For the Developer (You)

### 1. Build the Docker Image

```bash
# Navigate to your project directory
cd /path/to/sunmax-renewables

# Build the Docker image
docker build -t sunmax-renewables:latest .
```

### 2. Test the Docker Image Locally

```bash
# Run the container locally to test
docker run -p 8080:8080 -d --name sunmax-test sunmax-renewables:latest

# Check if the container is running
docker ps

# View logs to check for any errors
docker logs sunmax-test

# Access the application at http://localhost:8080
```

### 3. Tag the Image for Docker Hub

```bash
# Replace 'yourusername' with your Docker Hub username
docker tag sunmax-renewables:latest shaik07/sunmax-renewables:latest
```

### 4. Log in to Docker Hub

```bash
# Log in to Docker Hub
docker login
# Enter your Docker Hub username and password when prompted
```

### 5. Push the Image to Docker Hub

```bash
# Push the image to Docker Hub
docker push shaik07/sunmax-renewables:latest
```

## For Your Friend

### 1. Install Docker

If Docker is not already installed, follow the instructions for your operating system:
- [Install Docker on Windows](https://docs.docker.com/desktop/install/windows-install/)
- [Install Docker on macOS](https://docs.docker.com/desktop/install/mac-install/)
- [Install Docker on Linux](https://docs.docker.com/engine/install/)

### 2. Pull the Docker Image

```bash
# Replace 'yourusername' with the Docker Hub username where the image is hosted
docker pull shaik07/sunmax-renewables:latest
```

### 3. Run the Container

```bash
# Create a directory for persistent data
mkdir -p ~/sunmax-data/db

# Run the container with a volume mount for the database
docker run -p 8080:8080 -d \
  -v ~/sunmax-data/db:/app/db \
  -v ~/sunmax-data/invoices:/app/invoices \
  -v ~/sunmax-data/exports:/app/exports \
  --name sunmax-renewables \
  yourusername/sunmax-renewables:latest
```

### 4. Access the Application

Open your web browser and navigate to:
```
http://localhost:8080
```

### 5. Default Login Credentials

- Username: contactsunmax@gmail.com
- Password: Sunmax@123

**Important**: Change the default password immediately after first login.

### 6. Managing the Container

```bash
# Stop the container
docker stop sunmax-renewables

# Start the container again
docker start sunmax-renewables

# Remove the container (will not delete your data if you used volume mounts)
docker rm sunmax-renewables

# View logs
docker logs sunmax-renewables

# Update to the latest version
docker pull yourusername/sunmax-renewables:latest
docker stop sunmax-renewables
docker rm sunmax-renewables
# Then run the container again with the same command as in step 3
```

## Managing Docker Images and Containers

### Checking Docker Images

```bash
# List all Docker images
docker images

# The output will look like:
# REPOSITORY                      TAG       IMAGE ID       CREATED         SIZE
# yourusername/sunmax-renewables  latest    abc123def456   2 hours ago     350MB
# python                          3.9-slim  789ghi101112   3 weeks ago     125MB
```

### Checking Running Containers

```bash
# List all running containers
docker ps

# List all containers (including stopped ones)
docker ps -a
```

### Stopping Containers

```bash
# Stop a running container
docker stop sunmax-renewables

# Stop all running containers
docker stop $(docker ps -q)
```

### Removing Containers

```bash
# Remove a specific container (must be stopped first)
docker rm sunmax-renewables

# Remove all stopped containers
docker container prune

# Force remove a running container (use with caution)
docker rm -f sunmax-renewables
```

### Removing Images

```bash
# Remove a specific image
docker rmi yourusername/sunmax-renewables:latest

# Remove all unused images
docker image prune

# Remove all images not used by containers
docker image prune -a
```

### Cleaning Up Everything

```bash
# Remove all stopped containers, unused networks, dangling images, and build cache
docker system prune

# Remove all stopped containers, all networks not used, all images without containers, and build cache
docker system prune -a
```

## Troubleshooting

### Database Issues

If you encounter database errors:

```bash
# Access the container shell
docker exec -it sunmax-renewables /bin/bash

# Inside the container, run the database migration
python migrate_db.py

# Exit the container shell
exit
```

### Permission Issues

If you encounter permission issues with the mounted volumes:

```bash
# Fix permissions on the host
sudo chown -R 1000:1000 ~/sunmax-data
```

### Container Won't Start

Check the logs for errors:

```bash
docker logs sunmax-renewables
```

## Data Backup

To backup your data:

```bash
# Create a backup directory
mkdir -p ~/sunmax-backups

# Copy the database and other important files
cp -r ~/sunmax-data/db ~/sunmax-backups/db_$(date +%Y%m%d)
cp -r ~/sunmax-data/invoices ~/sunmax-backups/invoices_$(date +%Y%m%d)
cp -r ~/sunmax-data/exports ~/sunmax-backups/exports_$(date +%Y%m%d)
```
