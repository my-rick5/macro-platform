# --- STAGE 1: DataPrep (The "Bake-In" Phase) ---
FROM debian:12-slim AS dataprep

USER root
# Apply GPG bypass for network/proxy issues
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
# Added libxml2-dev and libxslt-dev for the 'lxml' dependency
RUN echo "Acquire::Check-Valid-Until \"false\";\nAcquire::Check-Date \"false\";" > /etc/apt/apt.conf.d/99ignore-security && \
    apt-get update --allow-insecure-repositories || true && \
    apt-get install -y --allow-unauthenticated --no-install-recommends \
    openjdk-17-jre-headless python3 python3-pip \
    libsuitesparse-dev libatlas3-base libblas3 liblapack3 \
    libxml2-dev libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install production dependencies
# Adding lxml explicitly here to ensure it builds correctly
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt && \
    pip3 install --no-cache-dir --break-system-packages lxml

RUN groupadd -g 1099 spark && useradd -u 1099 -g 1099 -d /home/spark -m spark

# --- DATA & MODULE INJECTION ---

# 1. Copy the nested pyfrbus package (pyfrbus/pyfrbus/...)
COPY --chown=spark:spark pyfrbus /home/spark/pyfrbus

# 2. Copy the raw external data (longdata.csv)
COPY --chown=spark:spark external_data /home/spark/external_data

# 3. Copy the original Excel library
COPY --chown=spark:spark data/library.xlsx /home/spark/data/library.xlsx

# 4. Inject the BAKED-IN clean CSVs from Stage 1
COPY --from=dataprep --chown=spark:spark /build/processed/ /home/spark/external_data/

# --- FINAL SETUP ---
COPY --chown=spark:spark src /home/spark/src
COPY --chown=spark:spark pyfrbus/models /home/spark/models

RUN mkdir -p /home/spark/results && chown spark:spark /home/spark/results
WORKDIR /home/spark
USER spark

# CRITICAL: Path includes both root and the nested folder to handle the double-pyfrbus structure
ENV PYTHONPATH="/home/spark:/home/spark/pyfrbus"

CMD ["python3", "src/engine.py"]