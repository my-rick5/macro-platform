import os
import pandas as pd

def fetch_and_verify_macro_data():
    data_dir = "/home/spark/data"
    local_xlsx = os.path.join(data_dir, "tealbook_raw.xlsx")
    output_csv = os.path.join(data_dir, "tealbook_full_x.csv")
    
    # We are pulling the 'Big Three' to feed the model's endogenous loops
    sheet_map = {
        'unemp_x': 'RUC',      # Unemployment Rate
        'gdp_growth_x': 'gRGDP', # Real GDP Growth
        'pce_inf_x': 'gPPCE'    # PCE Inflation
    }

    final_df = pd.DataFrame()

    print("🔍 Beginning data extraction and verification...")

    for var_name, sheet in sheet_map.items():
        try:
            # Read only what we need
            df = pd.read_excel(local_xlsx, sheet_name=sheet, engine='openpyxl')
            
            # Extract Meeting Date and Nowcast (Q0)
            temp = df[['Date of Meeting', 'Q0']].copy()
            temp.columns = ['date', var_name]
            
            # --- DEBUGGING LOGIC ---
            # 1. Check for 'Date Leakage' (Excel dates are usually > 40,000)
            sample_val = temp[var_name].dropna().iloc[-1]
            if sample_val > 50: 
                print(f"❌ ERROR: {var_name} appears to be a date index ({sample_val}), not a macro value!")
            else:
                print(f"✅ {var_name} verified. Sample: {sample_val}%")

            # 2. Convert to datetime for merging
            temp['date'] = pd.to_datetime(temp['date'])
            
            # Merge logic
            if final_df.empty:
                final_df = temp
            else:
                final_df = pd.merge(final_df, temp, on='date', how='outer')
                
        except Exception as e:
            print(f"⚠️  Failed to process sheet {sheet}: {e}")

    # Save the consolidated X-Vector
    final_df.sort_values('date', inplace=True)
    final_df.to_csv(output_csv, index=False)
    print(f"\n✨ Successfully merged {len(final_df)} quarters of data into {output_csv}")

if __name__ == "__main__":
    fetch_and_verify_macro_data()