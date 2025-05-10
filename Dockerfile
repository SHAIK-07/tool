FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Remove GCP environment variable
# ENV IN_GCP=true

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install uv for package management
RUN pip install --no-cache-dir uv

# Install Python dependencies with uv
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt
# Explicitly install itsdangerous to ensure it's available
RUN uv pip install --system itsdangerous

# Copy application code
COPY . .

# Copy the admin user scripts
COPY ensure_admin_user.py /app/ensure_admin_user.py
COPY create_admin.py /app/create_admin.py

# Create necessary directories with proper permissions
RUN mkdir -p /app/invoices /app/exports /app/db && \
    chmod -R 777 /app/invoices /app/exports /app/db

# Make sure SQLite database directory is writable
RUN touch /app/db/sunmax.db && chmod 666 /app/db/sunmax.db

# Create a simplified startup script
COPY <<EOF /app/startup.sh
#!/bin/bash
echo "Starting server..."

# Install missing packages if needed (using uv)
echo "Installing required packages..."
uv pip install --system python-dotenv itsdangerous passlib[bcrypt] bcrypt pydantic[email] email-validator

# Create db directory if it doesn't exist
echo "Ensuring db directory exists..."
mkdir -p /app/db

# Check if we need to initialize the database
echo "Checking if database exists..."
if [ ! -f "/app/db/sunmax.db" ]; then
  echo "Database not found, creating a new one..."
  touch /app/db/sunmax.db
  chmod 666 /app/db/sunmax.db
fi

echo "Using database in /app/db/sunmax.db"

# Ensure admin user exists
echo "Ensuring admin user exists..."
python /app/ensure_admin_user.py

# Force create admin user (more aggressive approach)
echo "Directly creating admin user..."
python /app/create_admin.py

# Start the application
echo "Starting the application..."
exec uvicorn app.main:app --host=0.0.0.0 --port=8080 --timeout-keep-alive 75
EOF
RUN chmod +x /app/startup.sh

# Run the application
CMD ["/app/startup.sh"]


