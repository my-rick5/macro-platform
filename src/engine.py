import pandas as pd
import os

def run_macro_engine():
    # Paths inside the Docker container
    input_xlsx = "/home/spark/data/tealbook_raw.xlsx"
    output_path = "/home/spark/results/forecast_summary.csv"
    
    if not os.path.exists(input_xlsx):
        print(f"❌ Error: {input_xlsx} not found inside container.")
        return

    print(f"📖 Reading data from {input_xlsx}...")
    # Load the new 'UNEMP' sheet
    df = pd.read_excel(input_xlsx, sheet_name='UNEMP')
    
    # Get the latest row (vintage)
    latest_vintage = df.iloc[-1]
    vintage_date = latest_vintage.iloc[0]
    
    # Calculate mean of the forecast columns
    mean_forecast = pd.to_numeric(latest_vintage.iloc[1:], errors='coerce').mean()

    results_df = pd.DataFrame([{
        "vintage": vintage_date,
        "mean_unemployment_forecast": round(mean_forecast, 2)
    }])

    results_df.to_csv(output_path, index=False)
    print(f"✅ Success! Forecast summary saved to {output_path}")

if __name__ == "__main__":
    run_macro_engine()