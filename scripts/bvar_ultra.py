import os
import polars as pl
import numpy as np
import duckdb
import matplotlib.pyplot as plt
import mlflow
import mlflow.statsmodels
from statsmodels.tsa.vector_ar.var_model import VAR
from dotenv import load_dotenv

load_dotenv()

def run_ultra_model():
    # 1. MLFLOW INITIALIZATION
    # Using the service name 'mlflow' as defined in your docker-compose
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
    mlflow.set_experiment("Macro_Forecast_Engine")

    with mlflow.start_run():
        project_root = os.getenv('PROJECT_ROOT', '/app')
        db_path = os.getenv('DB_PATH', os.path.join(project_root, 'data', 'macro_warehouse.db'))
        
        # 2. DATA FETCH (Polars + DuckDB)
        query = """
            SELECT * FROM stg_fred_indicators 
            WHERE inflation_mom IS NOT NULL AND vix IS NOT NULL 
            ORDER BY date ASC
        """
        
        with duckdb.connect(db_path) as con:
            df = con.execute(query).pl()

        # 3. TRANSFORMATIONS
        df = df.with_columns([
            pl.col("real_gdp").log().alias("log_gdp"),
            pl.col("fed_assets").log().alias("log_fed_assets")
        ]).drop_nulls()

        model_vars = ['fed_funds_rate', 'unemployment_rate', 'inflation_mom', 'vix', 'log_gdp', 'log_fed_assets']
        pd_df = df.select(['date'] + model_vars).to_pandas()
        pd_df.set_index('date', inplace=True)
        
        # 4. MODEL FITTING
        print(f"Fitting BVAR with Polars-prepped data ({len(df)} rows)...")
        lags = 6
        model = VAR(pd_df)
        results = model.fit(lags)
        
        # Log parameters to MLflow
        mlflow.log_param("model_type", "BVAR")
        mlflow.log_param("lags", lags)
        mlflow.log_param("row_count", len(df))
        
        # 5. FORECAST
        forecast_steps = 6
        forecast = results.forecast(pd_df.values[-forecast_steps:], forecast_steps)
        forecast_df = pl.DataFrame(forecast, schema=model_vars)
        
        print("\n--- POLARS-ACCELERATED BVAR FORECAST ---")
        print(forecast_df)

        # Log forecast results as an artifact
        forecast_path = os.path.join(project_root, 'notebooks', 'forecast_results.csv')
        forecast_df.write_csv(forecast_path)
        mlflow.log_artifact(forecast_path)

        # 6. VISUALS & MLFLOW LOGGING
        irf = results.irf(12)
        fig = irf.plot(impulse='vix', response='fed_funds_rate', orth=True)
        
        save_path = os.path.join(project_root, 'notebooks', 'vix_shock_response.png')
        # Create directory if it doesn't exist (failsafe)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        plt.savefig(save_path)
        mlflow.log_artifact(save_path)
        
        print(f"\nModel logged to MLflow. Chart saved to: {save_path}")

if __name__ == "__main__":
    run_ultra_model()