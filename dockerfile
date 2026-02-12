# --- STAGE 1: DataPrep (The "Bake-In" Phase) ---
FROM debian:12-slim AS dataprep

USER root
# 1. Force GPG bypass and install Python for preprocessing
RUN echo "Acquire::Check-Valid-Until \"false\";\nAcquire::Check-Date \"false\";" > /etc/apt/apt.conf.d/99ignore-security && \
    apt-get update --allow-insecure-repositories || true && \
    apt-get install -y --allow-unauthenticated --no-install-recommends \
    python3 python3-pip && rm -rf /var/lib/apt/lists/*

# 2. Install preprocessor requirements
RUN pip3 install --break-system-packages pandas openpyxl

WORKDIR /build
COPY src/preprocess.py .
COPY data/library.xlsx .

# 3. Create the clean CSVs (unemp.csv, gdp.csv, etc.)
RUN mkdir processed && python3 preprocess.py


# --- STAGE 2: Final Runtime ---
FROM debian:12-slim

USER root
# 1. Apply same GPG bypass and install Java + Python + Math libs
RUN echo "Acquire::Check-Valid-Until \"false\";\nAcquire::Check-Date \"false\";" > /etc/apt/apt.conf.d/99ignore-security && \
    apt-get update --allow-insecure-repositories || true && \
    apt-get install -y --allow-unauthenticated --no-install-recommends \
    openjdk-17-jre-headless python3 python3-pip \
    libsuitesparse-dev libatlas3-base libblas3 liblapack3 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install production python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# 3. Setup Spark user
RUN groupadd -g 1099 spark && useradd -u 1099 -g 1099 -d /home/spark -m spark

# --- DATA INJECTION (The Critical Part) ---

# A. Copy the raw external_data (contains longdata.csv)
COPY --chown=spark:spark external_data /home/spark/external_data

# B. Copy the original Excel library (in case engine needs to read it)
COPY --chown=spark:spark data/library.xlsx /home/spark/data/library.xlsx

# C. Inject the BAKED clean CSVs from Stage 1 into the engine's data path
# This populates /home/spark/external_data/ with unemp.csv, gdp.csv, etc.
COPY --from=dataprep --chown=spark:spark /build/processed/ /home/spark/external_data/

# --- LOGIC INJECTION ---
COPY --chown=spark:spark src /home/spark/src
COPY --chown=spark:spark pyfrbus/models /home/spark/models

# Setup workspace
RUN mkdir -p /home/spark/results && chown spark:spark /home/spark/results
WORKDIR /home/spark
USER spark
ENV PYTHONPATH="/home/spark"

CMD ["python3", "src/engine.py"]