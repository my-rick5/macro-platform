# Use a high-performance slim image
FROM python:3.10-slim

# Install system dependencies for Polars and Statsmodels
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy dependency list and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project structure
COPY scripts/ ./scripts/
COPY dbt_macro/ ./dbt_macro/
# We don't copy 'data/' because we will mount it as a volume

# Set Environment Variables
ENV PYTHONUNBUFFERED=1

# The container doesn't "do" anything until we tell it to via 'docker run'
