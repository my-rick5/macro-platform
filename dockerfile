# --- STAGE 1: DataPrep ---
FROM debian:11-slim AS dataprep
USER root
RUN echo "Acquire::Check-Valid-Until \"false\";\nAcquire::Check-Date \"false\";" > /etc/apt/apt.conf.d/99ignore-security && \
    apt-get update || true && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install --break-system-packages pandas openpyxl
WORKDIR /build
COPY src/preprocess.py .
COPY data/library.xlsx .
RUN mkdir processed && python3 preprocess.py

# --- STAGE 2: Final Runtime ---
FROM debian:11-slim
USER root
RUN echo "Acquire::Check-Valid-Until \"false\";\nAcquire::Check-Date \"false\";" > /etc/apt/apt.conf.d/99ignore-security && \
    apt-get update || true && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless python3 python3-pip \
    libsuitesparse-dev libatlas3-base libblas3 liblapack3 \
    libxml2-dev libxslt-dev \
    libsymengine-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies + symengine
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt && \
    pip3 install --no-cache-dir --break-system-packages lxml symengine

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

# Point PYTHONPATH directly to the repo root and the inner code folder
ENV PYTHONPATH="/home/spark/pyfrbus"

CMD ["python3", "src/engine.py"]