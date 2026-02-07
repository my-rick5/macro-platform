{{ config(materialized='table') }}

WITH raw_data AS (
    SELECT 
        regexp_extract(filename::VARCHAR, 'raw/(.*)\.parquet', 1) as series_id,
        "date"::TIMESTAMP as observation_date,
        "value"::DOUBLE as observation_value
    FROM read_parquet(
        '{{ var("raw_data_path") }}/*.parquet', 
        union_by_name=True,
        filename=True 
    )
),

pivoted AS (
    SELECT
        observation_date as date,
        MAX(CASE WHEN series_id = 'FEDFUNDS' THEN observation_value END) as fed_funds_rate,
        MAX(CASE WHEN series_id = 'CPIAUCSL' THEN observation_value END) as cpi,
        MAX(CASE WHEN series_id = 'GDPC1' THEN observation_value END) as gdp,
        MAX(CASE WHEN series_id = 'UNRATE' THEN observation_value END) as unemployment_rate,
        MAX(CASE WHEN series_id = 'VIXCLS' THEN observation_value END) as vix,
        MAX(CASE WHEN series_id = 'WALCL' THEN observation_value END) as fed_assets
    FROM raw_data
    GROUP BY 1
)

SELECT
    date,
    fed_funds_rate,
    unemployment_rate,
    -- Monthly Inflation calculation
    (cpi / lag(cpi) over (order by date) - 1) * 100 as inflation_mom,
    -- Forward Fill logic with names matching your Python script
    last_value(gdp ignore nulls) over (order by date rows between unbounded preceding and current row) as real_gdp,
    last_value(vix ignore nulls) over (order by date rows between unbounded preceding and current row) as vix,
    last_value(fed_assets ignore nulls) over (order by date rows between unbounded preceding and current row) as fed_assets
FROM pivoted
ORDER BY date DESC