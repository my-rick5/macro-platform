import os
import polars as pl
import numpy as np
import duckdb
import matplotlib.pyplot as plt
from statsmodels.tsa.vector_ar.var_model import VAR
from dotenv import load_dotenv

load_dotenv()

def run_ultra_model():
    project_root = os.getenv('PROJECT_ROOT', os.getcwd())
    db_path = os.getenv('DB_PATH', os.path.join(project_root, 'data', 'macro_warehouse.db'))
    
    # 1. POLARS DATA FETCH (Using DuckDB as the engine)
    # We use pl.read_database for high-speed transfer from DuckDB to Polars
    query = """
        SELECT * FROM stg_fred_indicators 
        WHERE inflation_mom IS NOT NULL AND vix IS NOT NULL 
        ORDER BY date ASC
    """
    
    # Connect and pull into a Polars DataFrame
    with duckdb.connect(db_path) as con:
        df = con.execute(query).pl()

    # 2. POLARS TRANSFORMATIONS (The "Beyond Prototype" way)
    # Fast, vectorized log transformations
    df = df.with_columns([
        pl.col("real_gdp").log().alias("log_gdp"),
        pl.col("fed_assets").log().alias("log_fed_assets")
    ]).drop_nulls()

    # 3. PREP FOR STATSMODELS
    # Note: Statsmodels still requires a Pandas-like index for BVAR math, 
    # so we do a light conversion at the last possible second.
    model_vars = ['fed_funds_rate', 'unemployment_rate', 'inflation_mom', 'vix', 'log_gdp', 'log_fed_assets']
    
    # Convert to Pandas for the VAR engine (this is standard for statsmodels)
    pd_df = df.select(['date'] + model_vars).to_pandas()
    pd_df.set_index('date', inplace=True)
    
    # 4. THE BVAR BRAIN
    print(f"Fitting BVAR with Polars-prepped data ({len(df)} rows)...")
    model = VAR(pd_df)
    results = model.fit(6) 
    
    # 5. THE FORECAST
    forecast_steps = 6
    forecast = results.forecast(pd_df.values[-6:], forecast_steps)
    
    # Display the output
    print("\n--- POLARS-ACCELERATED BVAR FORECAST ---")
    forecast_df = pl.DataFrame(forecast, schema=model_vars)
    print(forecast_df)

    # 6. SAVE VISUALS
    irf = results.irf(12)
    irf.plot(impulse='vix', response='fed_funds_rate', orth=True)
    
    save_path = os.path.join(project_root, 'notebooks', 'vix_shock_response.png')
    plt.savefig(save_path)
    print(f"\nPolars build complete. Chart saved to: {save_path}")

if __name__ == "__main__":
    run_ultra_model()