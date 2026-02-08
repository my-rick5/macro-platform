# --- STAGE 1: Builder (Compilation & Dependency Resolution) ---
FROM debian:11-slim AS builder

USER root
ENV DEBIAN_FRONTEND=noninteractive \
    DEB_PYTHON_INSTALL_LAYOUT=standard \
    PATH="/root/.local/bin:${PATH}"

# 1. Install system dependencies + Build Tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    swig \
    libsuitesparse-dev \
    libatlas-base-dev \
    libblas-dev \
    liblapack-dev \
    pkg-config \
    gcc \
    g++ \
    gfortran \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# 2. Pre-install build backends and core math libraries
# Added openpyxl for Tealbook Excel processing
RUN pip3 install --upgrade pip && \
    pip3 install --user \
    setuptools \
    wheel \
    "meson-python>=0.11" \
    "meson>=1.0" \
    "numpy<2.0.0" \
    "scipy>=1.10,<1.14" \
    "openpyxl" 

# 3. Build scikit-umfpack 0.4.1 from source
RUN CFLAGS="-I/usr/include/suitesparse" \
    pip3 install scikit-umfpack==0.4.1 \
    --user \
    --no-build-isolation

# 4. Install requirements (Pandas, Pytest, SymPy, Requests, etc.)
COPY requirements.txt .
RUN pip3 install --user -r requirements.txt


# --- STAGE 2: Final Runtime (Minimal Environment) ---
FROM debian:11-slim

USER root
ENV DEBIAN_FRONTEND=noninteractive

# Install shared runtime libraries and JRE
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-11-jre-headless \
    python3 \
    python3-pip \
    libsuitesparse-dev \
    libatlas3-base \
    libblas3 \
    liblapack3 \
    && rm -rf /var/lib/apt/lists/*

# Setup application user
RUN groupadd -g 1099 spark && useradd -u 1099 -g 1099 -d /home/spark -m spark

# Copy compiled Python packages and core logic from Builder
COPY --from=builder /root/.local /home/spark/.local
COPY pyfrbus /home/spark/pyfrbus
COPY src /home/spark/src
COPY tests /home/spark/tests

# Create data and results directories with proper permissions
RUN mkdir -p /home/spark/data /home/spark/results && \
    chown -R spark:spark /home/spark

# Environment Configuration
ENV PYTHONPATH="/home/spark/.local/lib/python3.9/site-packages:/home/spark:${PYTHONPATH}" \
    PATH="/home/spark/.local/bin:${PATH}"

WORKDIR /home/spark
USER spark

# Default command
CMD ["python3", "src/engine.py"]