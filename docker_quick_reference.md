# Docker Quick Reference Guide

## Basic Docker Commands

### Images

| Command | Description |
|---------|-------------|
| `docker images` | List all images |
| `docker build -t name:tag .` | Build an image from a Dockerfile |
| `docker rmi image_id` | Remove an image |
| `docker pull repository:tag` | Pull an image from Docker Hub |
| `docker push repository:tag` | Push an image to Docker Hub |
| `docker tag source_image:tag target_image:tag` | Tag an image |
| `docker image prune` | Remove unused images |
| `docker image prune -a` | Remove all unused images |

### Containers

| Command | Description |
|---------|-------------|
| `docker ps` | List running containers |
| `docker ps -a` | List all containers (including stopped) |
| `docker run -p host:container image_name` | Run a container |
| `docker run -d image_name` | Run container in background |
| `docker run -v host_path:container_path image_name` | Run with volume mount |
| `docker start container_id` | Start a stopped container |
| `docker stop container_id` | Stop a running container |
| `docker restart container_id` | Restart a container |
| `docker rm container_id` | Remove a container |
| `docker rm -f container_id` | Force remove a running container |
| `docker container prune` | Remove all stopped containers |

### Logs & Exec

| Command | Description |
|---------|-------------|
| `docker logs container_id` | View container logs |
| `docker logs -f container_id` | Follow container logs |
| `docker exec -it container_id command` | Run command in container |
| `docker exec -it container_id /bin/bash` | Get shell in container |

### System

| Command | Description |
|---------|-------------|
| `docker info` | Display system-wide information |
| `docker version` | Show Docker version |
| `docker system df` | Show Docker disk usage |
| `docker system prune` | Remove unused data |
| `docker system prune -a` | Remove all unused data |

## Common Docker Run Options

| Option | Description |
|--------|-------------|
| `-d, --detach` | Run container in background |
| `-p, --publish host:container` | Publish container port to host |
| `-v, --volume host:container` | Bind mount a volume |
| `--name string` | Assign a name to the container |
| `-e, --env KEY=VALUE` | Set environment variables |
| `--rm` | Remove container when it exits |
| `--restart string` | Restart policy (no, always, on-failure, unless-stopped) |

## Docker Compose

| Command | Description |
|---------|-------------|
| `docker-compose up` | Create and start containers |
| `docker-compose up -d` | Create and start in background |
| `docker-compose down` | Stop and remove containers |
| `docker-compose ps` | List containers |
| `docker-compose logs` | View output from containers |
| `docker-compose build` | Build or rebuild services |

## Examples for Sunmax Renewables

### Build and Run

```bash
# Build the image
docker build -t sunmax-renewables:latest .

# Run the container
docker run -p 8080:8080 -d \
  -v ~/sunmax-data/db:/app/db \
  -v ~/sunmax-data/invoices:/app/invoices \
  -v ~/sunmax-data/exports:/app/exports \
  --name sunmax-renewables \
  sunmax-renewables:latest
```

### Push to Docker Hub

```bash
# Tag the image
docker tag sunmax-renewables:latest yourusername/sunmax-renewables:latest

# Push to Docker Hub
docker push yourusername/sunmax-renewables:latest
```

### Cleanup

```bash
# Stop and remove container
docker stop sunmax-renewables
docker rm sunmax-renewables

# Remove image
docker rmi yourusername/sunmax-renewables:latest
```
