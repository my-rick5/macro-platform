# --- STAGE 1: DataPrep ---
FROM debian:12-slim AS dataprep

USER root
# Apply GPG bypass for corporate proxy/network issues
RUN echo "Acquire::Check-Valid-Until \"false\";\nAcquire::Check-Date \"false\";" > /etc/apt/apt.conf.d/99ignore-security && \
    apt-get update --allow-insecure-repositories || true && \
    apt-get install -y --allow-unauthenticated --no-install-recommends \
    python3 python3-pip && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages pandas openpyxl

WORKDIR /build
COPY src/preprocess.py .
COPY data/library.xlsx .
RUN mkdir processed && python3 preprocess.py

# --- STAGE 2: Final Runtime ---
FROM debian:12-slim

USER root
RUN echo "Acquire::Check-Valid-Until \"false\";\nAcquire::Check-Date \"false\";" > /etc/apt/apt.conf.d/99ignore-security && \
    apt-get update --allow-insecure-repositories || true && \
    apt-get install -y --allow-unauthenticated --no-install-recommends \
    openjdk-17-jre-headless python3 python3-pip \
    libsuitesparse-dev libatlas3-base libblas3 liblapack3 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

RUN groupadd -g 1099 spark && useradd -u 1099 -g 1099 -d /home/spark -m spark

# 1. First, copy the entire external_data folder (contains longdata.csv)
COPY --chown=spark:spark external_data /home/spark/external_data

# 2. Then, inject ONLY the baked files from the builder into that same folder
# This prevents overwriting the whole directory and keeps longdata.csv safe
COPY --from=dataprep --chown=spark:spark /build/processed/ /home/spark/external_data/

# Copy remaining logic
COPY --chown=spark:spark src /home/spark/src
COPY --chown=spark:spark pyfrbus/models /home/spark/models

RUN mkdir -p /home/spark/results && chown spark:spark /home/spark/results
WORKDIR /home/spark
USER spark
ENV PYTHONPATH="/home/spark"

CMD ["python3", "src/engine.py"]