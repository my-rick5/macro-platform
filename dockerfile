# --- STAGE 1: DataPrep (Preprocessing logic) ---
FROM debian:11-slim AS dataprep
USER root
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install pandas openpyxl
WORKDIR /build
COPY src/preprocess.py .
COPY data/library.xlsx .
RUN mkdir processed && python3 preprocess.py

# --- STAGE 2: Builder (Compilation & Dependency Resolution) ---
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

# Install core math foundation with strict pins to avoid the 'Tester' name error
RUN pip3 install --upgrade pip && \
    pip3 install --user setuptools wheel "meson-python>=0.11" "meson>=1.0" \
    "numpy>=1.19,<1.24" "scipy>=1.10,<1.11"

# Build scikit-umfpack from source using the identified math headers
RUN CFLAGS="-I/usr/include/suitesparse" \
    pip3 install scikit-umfpack==0.4.1 --user --no-build-isolation

# Install project requirements
COPY requirements.txt .
RUN pip3 install --user -r requirements.txt

# --- STAGE 3: Final Runtime (Minimal Environment) ---
FROM debian:11-slim
USER root
ENV DEBIAN_FRONTEND=noninteractive

# Install shared runtime libraries and JRE (Updated to OpenJDK 17)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless python3 python3-pip \
    libsuitesparse-dev libatlas3-base libblas3 liblapack3 \
    libxml2-dev libxslt-dev libgmp-dev libmpfr-dev libmpc-dev \
    && rm -rf /var/lib/apt/lists/*

# Setup application user
RUN groupadd -g 1099 spark && useradd -u 1099 -g 1099 -d /home/spark -m spark

# 1. Copy compiled Python packages from Builder
COPY --from=builder /root/.local /home/spark/.local

# 2. Inject core code and models
COPY --chown=spark:spark pyfrbus /home/spark/pyfrbus
RUN rm -f /home/spark/pyfrbus/__init__.py
COPY --chown=spark:spark src /home/spark/src
COPY --chown=spark:spark pyfrbus/models /home/spark/models

# 3. Inject Data (External + Preprocessed)
COPY --chown=spark:spark external_data /home/spark/external_data
COPY --chown=spark:spark data/library.xlsx /home/spark/data/library.xlsx
COPY --from=dataprep --chown=spark:spark /build/processed/ /home/spark/external_data/

# Finalize environment
RUN mkdir -p /home/spark/results && chown -R spark:spark /home/spark
WORKDIR /home/spark
USER spark

ENV PYTHONPATH="/home/spark/.local/lib/python3.9/site-packages:/home/spark" \
    PATH="/home/spark/.local/bin:${PATH}"

CMD ["python3", "src/engine.py"]