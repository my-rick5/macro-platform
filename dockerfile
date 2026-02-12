# --- STAGE 1: DataPrep ---
FROM debian:11-slim AS dataprep
USER root
RUN echo "Acquire::Check-Valid-Until \"false\";\nAcquire::Check-Date \"false\";" > /etc/apt/apt.conf.d/99ignore-security && \
    apt-get update || true && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install pandas openpyxl
WORKDIR /build
COPY src/preprocess.py .
COPY data/library.xlsx .
RUN mkdir processed && python3 preprocess.py

# --- STAGE 2: Final Runtime ---
FROM debian:11-slim
USER root

# 1. Install PRE-COMPILED math libraries and scikits via APT
# This bypasses the SWIG/Meson/NumPy build errors entirely.
RUN echo "Acquire::Check-Valid-Until \"false\";\nAcquire::Check-Date \"false\";" > /etc/apt/apt.conf.d/99ignore-security && \
    sed -i 's/main/main contrib non-free/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless python3 python3-pip python3-dev \
    # Key Fix: Install the pre-compiled Debian scikit-umfpack
    python3-numpy python3-scipy python3-scikits-umfpack \
    # System dependencies for other potential builds
    libsuitesparse-dev libatlas-base-dev \
    libxml2-dev libxslt-dev libgmp-dev libmpfr-dev libmpc-dev \
    build-essential gcc g++ && \
    apt-get install -y libsymengine-dev || echo "⚠️ Warning: libsymengine-dev not found" && \
    rm -rf /var/lib/apt/lists/*

# 2. Python dependency installation
COPY requirements.txt .

# IMPORTANT: We use --ignore-installed for system packages we want to keep (numpy/scipy)
# to prevent pip from trying to upgrade them to 2.0+ which would break the scikit.
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir lxml symengine networkx

# 3. User setup
RUN groupadd -g 1099 spark && useradd -u 1099 -g 1099 -d /home/spark -m spark

# --- DATA & MODULE INJECTION ---
COPY --chown=spark:spark pyfrbus /home/spark/pyfrbus

# FIX: Remove the outer __init__.py so Python looks at the inner pyfrbus package
RUN rm -f /home/spark/pyfrbus/__init__.py

COPY --chown=spark:spark external_data /home/spark/external_data
COPY --chown=spark:spark data/library.xlsx /home/spark/data/library.xlsx
COPY --from=dataprep --chown=spark:spark /build/processed/ /home/spark/external_data/
COPY --chown=spark:spark src /home/spark/src
COPY --chown=spark:spark pyfrbus/models /home/spark/models

RUN mkdir -p /home/spark/results && chown spark:spark /home/spark/results
WORKDIR /home/spark
USER spark

# Point PYTHONPATH to /home/spark so 'import pyfrbus' finds the directory
ENV PYTHONPATH="/home/spark"

CMD ["python3", "src/engine.py"]