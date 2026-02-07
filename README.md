# 📈 MacroFlow Platform (v5)

An automated Macroeconomic Forecasting Engine using Bayesian Vector Autoregression (BVAR) to predict Fed Funds Rates (FFR) and Market Volatility (VIX).

## 🏗️ Architecture
The system is built as a self-contained pipeline running on **Google Cloud Run Jobs**.

* **Warehouse**: DuckDB (`/data/macro_warehouse.duckdb`) storing FRED staging data.
* **Engine**: `bvar_ultra.py` (VAR model with $p=6$ lags).
* **Archive**: Automated Parquet/CSV/PNG exports to Google Cloud Storage.
* **Evaluation**: `evaluate_performance.py` calculating Mean Absolute Error (MAE) against realized data.

## 🚀 Deployment & Execution

### Local Development
To run a forecast and performance check locally:
\`\`\`bash
# Ensure local DB path is set
DB_PATH="./data/macro_warehouse.duckdb" python3 scripts/bvar_ultra.py && \
DB_PATH="./data/macro_warehouse.duckdb" python3 scripts/evaluate_performance.py
\`\`\`

### Cloud Production (v5)
The platform is containerized via Docker. To push updates:
\`\`\`bash
docker build --platform linux/amd64 -t us-central1-docker.pkg.dev/macroflow-486515/macro-repo/macro-forecast:v5 .
docker push us-central1-docker.pkg.dev/macroflow-486515/macro-repo/macro-forecast:v5
\`\`\`

## 📂 File Structure
* \`scripts/bvar_ultra.py\`: Main model logic and GCS archiving.
* \* \* \* \* \* \* \* \* \* \* \* \* \* \* \* \* \* \* \* \* y reporting.
* \`output/\* \`output/\* \`output/\* \`output/\* \`output/\* \`outpuockerfile\`: Chained execution logic (Phase 1: Forecast -> Phase 2: Eval).

## 📊 Performance Tracking
The model generates a **Mean Absolute Error (MAE)** score during every run. 
* **FFR MAE < 0.35**: High accuracy.
* **VIX MAE < 2.50**: Reliable volatility trend.
