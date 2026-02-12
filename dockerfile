# --- STAGE 1: Builder ---
FROM debian:12-slim AS builder

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip && rm -rf /var/lib/apt/lists/*

# Force use of a clean pip environment
RUN pip3 install --break-system-packages pandas openpyxl

WORKDIR /build
COPY src/preprocess.py .
COPY data/library.xlsx .
RUN mkdir processed && python3 preprocess.py

# --- STAGE 2: Final Runtime ---
FROM debian:12-slim

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless python3 python3-pip \
    libsuitesparse-dev libatlas3-base libblas3 liblapack3 \
    && rm -rf /var/lib/apt/lists/*

# Install requirements directly
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

RUN groupadd -g 1099 spark && useradd -u 1099 -g 1099 -d /home/spark -m spark

# INJECT DATA FROM BUILDER
COPY --from=builder --chown=spark:spark /build/processed/ /home/spark/data/
COPY --from=builder --chown=spark:spark /build/processed/ /home/spark/external_data/

COPY --chown=spark:spark src /home/spark/src
COPY --chown=spark:spark pyfrbus/models /home/spark/models

RUN mkdir -p /home/spark/results && chown spark:spark /home/spark/results
WORKDIR /home/spark
USER spark
ENV PYTHONPATH="/home/spark"

CMD ["python3", "src/engine.py"]