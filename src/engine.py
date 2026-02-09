import pandas as pd
import os

def run_macro_engine():
    input_path = "data/tealbook_unemployment.csv"
    output_path = "results/forecast_summary.csv"
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found")
        return

    # Load the row-format data
    df = pd.read_excel("data/tealbook_raw.xlsx", sheet_name="UNEMP")
    
    # In row format, 'Date' is usually the first column
    # Let's calculate the mean forecast for the most recent vintage
    latest_vintage = df.iloc[-1]
    vintage_date = latest_vintage.iloc[0]
    # Filter out non-numeric columns for the mean
    numeric_forecasts = pd.to_numeric(latest_vintage.iloc[1:], errors='coerce')
    avg_unemp = numeric_forecasts.mean()

    results_df = pd.DataFrame([{
        "vintage": vintage_date,
        "mean_unemployment_forecast": avg_unemp
    }])

    results_df.to_csv(output_path, index=False)
    print(f"✅ Engine complete. Summary saved to {output_path}")

if __name__ == "__main__":
    run_macro_engine()