FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpng-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*
    
COPY requirements.txt .

# Force-install critical GCS and Data libs just in case
RUN pip install --no-cache-dir -r requirements.txt \
    streamlit gcsfs pyarrow polars google-cloud-storage

# Copy all files from local to /app
COPY . .

# Explicitly bind to 0.0.0.0 and the PORT env var
# We use 'python -m streamlit' to ensure the correct pathing
ENTRYPOINT ["python", "-m", "streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]