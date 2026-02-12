# --- STAGE 1: Builder (Data Preparation Only) ---
FROM debian:11-slim AS builder
USER root
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install pandas openpyxl
WORKDIR /build
COPY src/preprocess.py .
COPY data/library.xlsx .
RUN mkdir processed && python3 preprocess.py

# --- STAGE 2: Final Runtime ---
FROM debian:11-slim
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-11-jre-headless python3 python3-pip \
    libsuitesparse-dev libatlas3-base libblas3 liblapack3 \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies directly in the final image to guarantee they are found
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

RUN groupadd -g 1099 spark && useradd -u 1099 -g 1099 -d /home/spark -m spark

# INJECT THE CLEAN DATA FROM BUILDER
COPY --from=builder --chown=spark:spark /build/processed/ /home/spark/data/
COPY --from=builder --chown=spark:spark /build/processed/ /home/spark/external_data/

# Copy logic
COPY --chown=spark:spark src /home/spark/src
COPY --chown=spark:spark pyfrbus/models /home/spark/models

RUN mkdir -p /home/spark/results && chown spark:spark /home/spark/results
WORKDIR /home/spark
USER spark
ENV PYTHONPATH="/home/spark"

CMD ["python3", "src/engine.py"]