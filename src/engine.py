import pandas as pd
import os
import sys

def run_macro_engine():
    # The 'Process Data' stage in Jenkins saves the file here
    input_file = "data/tealbook_unemployment.csv"
    output_dir = "results"
    output_file = os.path.join(output_dir, "forecast_summary.csv")

    print(f"🚀 Starting Macro Engine...")

    # 1. Validation: Ensure input exists
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found. Ensure 'Process Data' stage succeeded.")
        sys.exit(1)

    # 2. Load Data
    try:
        # The Row Format CSV has the date in the first column
        df = pd.read_csv(input_file)
        print(f"📊 Loaded {len(df)} forecast vintages.")
        
        # 3. Processing Logic (Row Format specific)
        # In the Phil Fed Row Format, the first column is the 'Date' (e.g., 20040128)
        # The subsequent columns are the forecast values for different quarters.
        
        # Get the latest available vintage (the last row)
        latest_vintage = df.iloc[-1]
        vintage_date = latest_vintage.iloc[0]
        
        # Convert all other columns to numeric, ignoring the date column
        forecast_values = pd.to_numeric(latest_vintage.iloc[1:], errors='coerce').dropna()
        
        if forecast_values.empty:
            print(f"⚠️ Warning: No numeric forecast data found for vintage {vintage_date}")
            mean_forecast = 0.0
        else:
            mean_forecast = forecast_values.mean()

        # 4. Create Summary DataFrame
        summary_df = pd.DataFrame([{
            "vintage_date": str(int(vintage_date)),
            "mean_unemployment_forecast": round(mean_forecast, 2),
            "forecast_horizon_quarters": len(forecast_values)
        }])

        # 5. Output Results
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        summary_df.to_csv(output_file, index=False)
        print(f"✅ Success! Summary for vintage {vintage_date} saved to {output_file}")
        print(summary_df.to_string(index=False))

    except Exception as e:
        print(f"❌ Critical Engine Failure: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_macro_engine()