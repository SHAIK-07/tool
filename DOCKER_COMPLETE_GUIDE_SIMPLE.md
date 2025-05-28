# Complete Docker Guide - Sunmax Renewables

## 🎯 What This Guide Covers
1. **Dockerize the project** - Build Docker image
2. **Run locally** - Start container on your machine
3. **Stop/Start/Debug** - Manage the container
4. **Push to Docker Hub** - Share your image
5. **Pull and run on other systems** - Deploy anywhere

---

## 📋 Prerequisites

### Install Docker
- **Windows/Mac**: Download from [docker.com](https://www.docker.com/products/docker-desktop/)
- **Linux**: `sudo apt install docker.io` (Ubuntu/Debian)

### Verify Installation
```bash
docker --version
docker run hello-world
```

---

## 🔨 Part 1: Dockerize the Project

### Step 1: Navigate to Project Directory
```bash
cd /path/to/sunmax-renewables
# Verify you see: Dockerfile, requirements.txt, app/ folder
```

### Step 2: Build Docker Image
```bash
# Build the image (takes 5-10 minutes first time)
docker build -t sunmax-renewables:latest .

# Verify image was created
docker images | grep sunmax-renewables
```

---

## 🚀 Part 2: Run Locally

### Step 1: Create Data Directories
```bash
# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\sunmax-data\db"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\sunmax-data\invoices"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\sunmax-data\exports"

# Linux/macOS
mkdir -p ~/sunmax-data/{db,invoices,exports}
```

### Step 2: Run Container
```bash
# Windows (PowerShell)
docker run -p 8080:8080 -d `
  -v "$env:USERPROFILE\sunmax-data\db:/app/db" `
  -v "$env:USERPROFILE\sunmax-data\invoices:/app/invoices" `
  -v "$env:USERPROFILE\sunmax-data\exports:/app/exports" `
  --name sunmax-renewables `
  sunmax-renewables:latest

# Linux/macOS
docker run -p 8080:8080 -d \
  -v ~/sunmax-data/db:/app/db \
  -v ~/sunmax-data/invoices:/app/invoices \
  -v ~/sunmax-data/exports:/app/exports \
  --name sunmax-renewables \
  sunmax-renewables:latest
```

### Step 3: Access Application
- Open browser: `http://localhost:8080`
- Login: `contactsunmax@gmail.com` / `Sunmax@123`
- **Change password immediately!**

---

## 🔧 Part 3: Stop/Start/Debug

### Container Management
```bash
# Check if container is running
docker ps

# Stop container
docker stop sunmax-renewables

# Start container
docker start sunmax-renewables

# Restart container
docker restart sunmax-renewables

# Remove container (must stop first)
docker stop sunmax-renewables
docker rm sunmax-renewables
```

### Debugging
```bash
# View logs
docker logs sunmax-renewables

# View logs in real-time
docker logs -f sunmax-renewables

# Access container shell
docker exec -it sunmax-renewables /bin/bash

# Check container details
docker inspect sunmax-renewables

# Monitor resource usage
docker stats sunmax-renewables
```

### Common Issues & Solutions
```bash
# Port already in use? Use different port
docker run -p 8081:8080 -d ... # then access via :8081

# Container won't start? Check logs
docker logs sunmax-renewables

# Build failed? Clean build
docker build --no-cache -t sunmax-renewables:latest .

# Permission issues? (Linux/macOS)
sudo chown -R $USER:$USER ~/sunmax-data
```

---

## 📤 Part 4: Push to Docker Hub

### Step 1: Create Docker Hub Account
1. Go to [hub.docker.com](https://hub.docker.com)
2. Sign up for free account
3. Remember your username

### Step 2: Tag Image for Docker Hub
```bash
# Replace 'shaik07' with your Docker Hub username
docker tag sunmax-renewables:latest shaik07/sunmax-renewables:latest
```

### Step 3: Login and Push
```bash
# Login to Docker Hub
docker login
# Enter your username and password

# Push image to Docker Hub
docker push shaik07/sunmax-renewables:latest
```

### Step 4: Verify Upload
- Go to [hub.docker.com](https://hub.docker.com)
- Login and check your repositories
- You should see `sunmax-renewables` listed

---

## 📥 Part 5: Pull and Run on Other Systems

### For Your Friend/Other Systems

#### Step 1: Install Docker
Same as prerequisites above - install Docker on their system.

#### Step 2: Create Data Directories
```bash
# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\sunmax-data\db"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\sunmax-data\invoices"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\sunmax-data\exports"

# Linux/macOS
mkdir -p ~/sunmax-data/{db,invoices,exports}
```

#### Step 3: Pull and Run
```bash
# Pull image from Docker Hub
docker pull shaik07/sunmax-renewables:latest

# Run container (Windows PowerShell)
docker run -p 8080:8080 -d `
  -v "$env:USERPROFILE\sunmax-data\db:/app/db" `
  -v "$env:USERPROFILE\sunmax-data\invoices:/app/invoices" `
  -v "$env:USERPROFILE\sunmax-data\exports:/app/exports" `
  --name sunmax-renewables `
  shaik07/sunmax-renewables:latest

# Run container (Linux/macOS)
docker run -p 8080:8080 -d \
  -v ~/sunmax-data/db:/app/db \
  -v ~/sunmax-data/invoices:/app/invoices \
  -v ~/sunmax-data/exports:/app/exports \
  --name sunmax-renewables \
  shaik07/sunmax-renewables:latest
```

#### Step 4: Access Application
- Open browser: `http://localhost:8080`
- Login: `contactsunmax@gmail.com` / `Sunmax@123`

---

## 🔄 Update Process

### When You Make Code Changes
```bash
# 1. Stop and remove old container
docker stop sunmax-renewables
docker rm sunmax-renewables

# 2. Rebuild image
docker build -t sunmax-renewables:latest .

# 3. Tag for Docker Hub
docker tag sunmax-renewables:latest shaik07/sunmax-renewables:latest

# 4. Push updated image
docker push shaik07/sunmax-renewables:latest

# 5. Run new container locally
docker run -p 8080:8080 -d -v ~/sunmax-data/db:/app/db --name sunmax-renewables sunmax-renewables:latest
```

### For Others to Get Updates
```bash
# 1. Stop current container
docker stop sunmax-renewables
docker rm sunmax-renewables

# 2. Pull latest image
docker pull shaik07/sunmax-renewables:latest

# 3. Run new container
docker run -p 8080:8080 -d -v ~/sunmax-data/db:/app/db --name sunmax-renewables shaik07/sunmax-renewables:latest
```

---

## 💾 Data Management

### Backup Data
```bash
# Windows
Copy-Item -Recurse "$env:USERPROFILE\sunmax-data" "$env:USERPROFILE\sunmax-backup-$(Get-Date -Format 'yyyyMMdd')"

# Linux/macOS
cp -r ~/sunmax-data ~/sunmax-backup-$(date +%Y%m%d)
```

### Restore Data
```bash
# Stop container first
docker stop sunmax-renewables

# Restore data
# Windows: Copy-Item -Recurse "backup-path\*" "$env:USERPROFILE\sunmax-data\"
# Linux/macOS: cp -r /backup-path/* ~/sunmax-data/

# Start container
docker start sunmax-renewables
```

---

## 🎯 Quick Reference Commands

### Essential Commands
```bash
# Build image
docker build -t sunmax-renewables:latest .

# Run container
docker run -p 8080:8080 -d -v ~/sunmax-data/db:/app/db --name sunmax-renewables sunmax-renewables:latest

# Check status
docker ps

# View logs
docker logs sunmax-renewables

# Stop/Start
docker stop sunmax-renewables
docker start sunmax-renewables

# Push to Docker Hub
docker tag sunmax-renewables:latest shaik07/sunmax-renewables:latest
docker push shaik07/sunmax-renewables:latest

# Pull from Docker Hub
docker pull shaik07/sunmax-renewables:latest
```

### One-Liner for New Systems
```bash
# Linux/macOS
mkdir -p ~/sunmax-data/db && docker pull shaik07/sunmax-renewables:latest && docker run -p 8080:8080 -d -v ~/sunmax-data/db:/app/db --name sunmax-renewables shaik07/sunmax-renewables:latest

# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\sunmax-data\db"; docker pull shaik07/sunmax-renewables:latest; docker run -p 8080:8080 -d -v "$env:USERPROFILE\sunmax-data\db:/app/db" --name sunmax-renewables shaik07/sunmax-renewables:latest
```

---

## 🆘 Troubleshooting

### Common Problems
1. **Port 8080 busy**: Use `-p 8081:8080` instead
2. **Container won't start**: Check `docker logs sunmax-renewables`
3. **Can't access app**: Verify container is running with `docker ps`
4. **Build fails**: Try `docker build --no-cache -t sunmax-renewables:latest .`
5. **Permission denied**: On Linux/macOS, run `sudo chown -R $USER:$USER ~/sunmax-data`

### Reset Everything
```bash
# Nuclear option - start completely fresh
docker stop sunmax-renewables
docker rm sunmax-renewables
docker rmi sunmax-renewables:latest shaik07/sunmax-renewables:latest
rm -rf ~/sunmax-data  # CAUTION: Deletes all data!
# Then start over with build commands
```

---

## ✅ Success Checklist

You know everything is working when:
- ✅ `docker ps` shows container running
- ✅ `docker logs sunmax-renewables` shows "Application startup complete"
- ✅ Browser loads http://localhost:8080
- ✅ You can login with default credentials
- ✅ Dashboard shows all features working

**That's it! You now have a complete Docker workflow for the Sunmax Renewables application.** 🎉
