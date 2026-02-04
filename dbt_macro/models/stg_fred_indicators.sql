{{ config(materialized='table') }}

with dates as (
    -- We use Fed Funds as our primary monthly date spine
    select date from read_parquet('../data/raw/FEDFUNDS.parquet')
),
ff as (select date, value from read_parquet('../data/raw/FEDFUNDS.parquet')),
cpi as (select date, value from read_parquet('../data/raw/CPIAUCSL.parquet')),
gdp as (select date, value from read_parquet('../data/raw/GDPC1.parquet')),
unemp as (select date, value from read_parquet('../data/raw/UNRATE.parquet')),
vix as (select date, value from read_parquet('../data/raw/VIXCLS.parquet')),
bal as (select date, value from read_parquet('../data/raw/WALCL.parquet'))

select
    d.date,
    ff.value as fed_funds_rate,
    unemp.value as unemployment_rate,
    -- Calculate Monthly Inflation
    (cpi.value / lag(cpi.value) over (order by d.date) - 1) * 100 as inflation_mom,
    -- Forward Fill the quarterly/weekly/daily gaps
    last_value(gdp.value ignore nulls) over (order by d.date) as real_gdp,
    last_value(vix.value ignore nulls) over (order by d.date) as vix,
    last_value(bal.value ignore nulls) over (order by d.date) as fed_assets
from dates d
left join ff on d.date = ff.date
left join cpi on d.date = cpi.date
left join gdp on d.date = gdp.date
left join unemp on d.date = unemp.date
left join vix on d.date = vix.date
left join bal on d.date = bal.date
