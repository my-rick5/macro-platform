# --- STAGE 1: Builder (Compilation & Dependency Resolution) ---
FROM debian:11-slim AS builder

USER root
ENV DEBIAN_FRONTEND=noninteractive \
    DEB_PYTHON_INSTALL_LAYOUT=standard \
    PATH="/root/.local/bin:${PATH}"

# 1. Install system dependencies + Build Tools for SciPy/UMFPACK stack
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

# 2. Pre-install build backends and core math libraries
# NOTE: NumPy < 2.0.0 is required for scikit-umfpack 0.4.x compatibility
RUN pip3 install --upgrade pip && \
    pip3 install --user \
    setuptools \
    wheel \
    "meson-python>=0.11" \
    "meson>=1.0" \
    "numpy<2.0.0" \
    "scipy>=1.10,<1.14"

# 3. Build scikit-umfpack 0.4.1 from source
# Using 0.4.1 to avoid specific SWIG bugs found in 0.4.2
RUN CFLAGS="-I/usr/include/suitesparse" \
    pip3 install scikit-umfpack==0.4.1 \
    --user \
    --no-build-isolation

# 4. Install the core data-science and modeling stack
RUN pip3 install --user \
    "pandas<2.1.0" \
    gcsfs \
    pyarrow \
    sympy \
    symengine \
    lxml \
    networkx

# --- STAGE 2: Final Runtime (Minimal Environment) ---
FROM debian:11-slim

USER root
ENV DEBIAN_FRONTEND=noninteractive

# Install shared runtime libraries only (keeps the image size down)
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

# Fix permissions
RUN chown -R spark:spark /home/spark

# Environment Configuration
# Adding /home/spark ensures 'import pyfrbus' works from the src directory
# Environment Configuration
# Adding /home/spark ensures 'import pyfrbus' works from the src directory
ENV PYTHONPATH="/home/spark/.local/lib/python3.9/site-packages:/home/spark:${PYTHONPATH}" \
    PATH="/home/spark/.local/bin:${PATH}"