# --- STAGE 1: Builder ---
FROM debian:11-slim AS builder

USER root
ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/root/.local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev swig libsuitesparse-dev \
    libatlas-base-dev libblas-dev liblapack-dev pkg-config \
    gcc g++ gfortran ninja-build && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# 1. Install Build Tools & Preprocessor Dependencies
RUN pip3 install --upgrade pip && \
    pip3 install --user \
    setuptools wheel "meson-python>=0.11" "meson>=1.0" \
    "numpy<2.0.0" "scipy>=1.10,<1.14" "openpyxl" "pandas"

# 2. Build scikit-umfpack
RUN CFLAGS="-I/usr/include/suitesparse" \
    pip3 install scikit-umfpack==0.4.1 --user --no-build-isolation

# 3. BAKE-IN DATA: Run preprocessor during image build
COPY src/preprocess.py /build/preprocess.py
COPY data/library.xlsx /build/library.xlsx
RUN mkdir -p /build/processed && \
    python3 /build/preprocess.py

# 4. Install requirements & pyfrbus
COPY requirements.txt .
RUN pip3 install --user -r requirements.txt
COPY pyfrbus /build/pyfrbus
RUN cd /build/pyfrbus && pip3 install --user .

# --- STAGE 2: Final Runtime ---
FROM debian:11-slim

USER root
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-11-jre-headless python3 python3-pip \
    libsuitesparse-dev libatlas3-base libblas3 liblapack3 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1099 spark && useradd -u 1099 -g 1099 -d /home/spark -m spark

# Copy compiled Python packages
COPY --from=builder /root/.local /home/spark/.local

# INJECT THE CLEAN DATA: Ensure it exists in every possible engine path
COPY --from=builder --chown=spark:spark /build/processed/ /home/spark/data/
COPY --from=builder --chown=spark:spark /build/processed/ /home/spark/external_data/

# Copy logic and remaining assets
COPY --chown=spark:spark src /home/spark/src
COPY --chown=spark:spark tests /home/spark/tests
COPY --chown=spark:spark pyfrbus/models /home/spark/models
COPY --chown=spark:spark data/library.xlsx /home/spark/data/library.xlsx

# Ensure results folder exists
RUN mkdir -p /home/spark/results && chown spark:spark /home/spark/results

# FLEXIBLE PYTHONPATH: Search both site-packages and dist-packages
ENV PYTHONPATH="/home/spark/.local/lib/python3.9/site-packages:/home/spark/.local/lib/python3/dist-packages:/home/spark:${PYTHONPATH}" \
    PATH="/home/spark/.local/bin:${PATH}"

WORKDIR /home/spark
USER spark

CMD ["python3", "src/engine.py"]