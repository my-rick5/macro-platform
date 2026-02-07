from fredapi import Fred
import polars as pl

def get_calibrated_wedge_data(api_key):
    fred = Fred(api_key=api_key)
    
    # 1. Fetch 20 Years of history
    cpi = fred.get_series('CPIAUCSL').to_frame(name='cpi')
    pce = fred.get_series('PCEPI').to_frame(name='pce')
    
    # 2. Convert to Polars for the 'Wedge' calculation
    df = pl.from_pandas(cpi.join(pce, how='inner').reset_index())
    
    # 3. Engineer Variable #3: The Stagnation Wedge
    df = df.with_columns([
        (pl.col("cpi").pct_change(12) * 100).alias("cpi_yoy"),
        (pl.col("pce").pct_change(12) * 100).alias("pce_yoy")
    ]).with_columns([
        (pl.col("cpi_yoy") - pl.col("pce_yoy")).alias("inflation_wedge")
    ]).drop(["cpi", "pce", "cpi_yoy", "pce_yoy"]).drop_nulls()
    
    return df
