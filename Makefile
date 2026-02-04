.PHONY: all ingest transform forecast

all: ingest transform forecast

ingest:
	@echo "Starting Ingestion..."
	python scripts/fred_ingestion.py

transform:
	@echo "Starting dbt Transformation..."
	cd dbt_macro && dbt run --profiles-dir .

forecast:
	@echo "Generating Forecast and Shocks..."
	python scripts/bvar_ultra.py
