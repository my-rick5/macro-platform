# --- STAGE 1: Builder (Compilation & Dependency Resolution) ---
FROM debian:11-slim AS builder

USER root
ENV DEBIAN_FRONTEND=noninteractive \
    DEB_PYTHON_INSTALL_LAYOUT=standard \
    PATH="/root/.local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev swig libsuitesparse-dev \
    libatlas-base-dev libblas-dev liblapack-dev pkg-config \
    gcc g++ gfortran ninja-build && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# 1. Pre-install build backends
RUN pip3 install --upgrade pip && \
    pip3 install --user \
    setuptools wheel "meson-python>=0.11" "meson>=1.0" \
    "numpy<2.0.0" "scipy>=1.10,<1.14" "openpyxl" 

# 2. Build scikit-umfpack (Required for FRB/US sparse matrix solving)
RUN CFLAGS="-I/usr/include/suitesparse" \
    pip3 install scikit-umfpack==0.4.1 --user --no-build-isolation

# 3. Install requirements
COPY requirements.txt .
RUN pip3 install --user -r requirements.txt

# 4. Install the actual pyfrbus package (Crucial for the 'Pro' Engine)
# This ensures it's installed in the site-packages we copy over
COPY pyfrbus /build/pyfrbus
RUN cd /build/pyfrbus && pip3 install --user .

# --- STAGE 2: Final Runtime (Minimal Environment) ---
FROM debian:11-slim

USER root
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-11-jre-headless python3 python3-pip \
    libsuitesparse-dev libatlas3-base libblas3 liblapack3 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1099 spark && useradd -u 1099 -g 1099 -d /home/spark -m spark

# Copy compiled Python packages and core logic
COPY --from=builder /root/.local /home/spark/.local
COPY src /home/spark/src
COPY tests /home/spark/tests

# Create data/results/models directories
# We need 'models' to house the model.xml we fetch in Jenkins
RUN mkdir -p /home/spark/data /home/spark/results /home/spark/models && \
    chown -R spark:spark /home/spark

ENV PYTHONPATH="/home/spark/.local/lib/python3.9/site-packages:/home/spark:${PYTHONPATH}" \
    PATH="/home/spark/.local/bin:${PATH}"

WORKDIR /home/spark
USER spark

CMD ["python3", "src/engine.py"]