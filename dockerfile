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
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# USE ABSOLUTE PATHS FOR COPY
COPY scripts/ /app/scripts/
COPY dbt_macro/ /app/dbt_macro/

# Set Environment Variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app