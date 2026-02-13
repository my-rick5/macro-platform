import os
import pandas as pd

def fetch_and_verify_macro_data():
    # 1. SETUP PATHS
    # We look for the file where Dockerfile COPIES it (root)
    # But we save results in the 'data' subfolder for the engine
    root_dir = os.getcwd()
    data_dir = os.path.join(root_dir, "data")
    
    # The source file from your Dockerfile COPY Step 3/7
    local_xlsx = os.path.join(root_dir, "library.xlsx") 
    output_csv = os.path.join(data_dir, "tealbook_full_x.csv")
    
    # Ensure the output directory exists
    os.makedirs(data_dir, exist_ok=True)

    print(f"🔍 Searching for source file: {local_xlsx}")

    # 2. SOURCE VERIFICATION
    if not os.path.exists(local_xlsx):
        # Fallback check: maybe it's in /data?
        fallback = os.path.join(data_dir, "library.xlsx")
        if os.path.exists(fallback):
            local_xlsx = fallback
        else:
            print(f"❌ ERROR: Source file not found at {local_xlsx}")
            print("Check your Dockerfile COPY command.")
            return

    # 3. DATA EXTRACTION
    sheet_map = {
        'unemp_x': 'RUC',      # Unemployment Rate
        'gdp_growth_x': 'gRGDP', # Real GDP Growth
        'pce_inf_x': 'gPPCE'    # PCE Inflation
    }

    final_df = pd.DataFrame()
    print("📡 Beginning extraction from Philadelphia Fed Sheets...")

    for var_name, sheet in sheet_map.items():
        try:
            # Read sheet - Philadelphia Fed sheets usually use row 0 for headers
            df = pd.read_excel(local_xlsx, sheet_name=sheet, engine='openpyxl')
            
            # Map columns - GBweb_Row_Format uses 'Date of Meeting' and 'Q0' (nowcast)
            # Adjust these strings if your specific version uses different headers
            date_col = 'Date of Meeting'
            val_col = 'Q0'

            if date_col not in df.columns:
                print(f"⚠️  Column '{date_col}' missing in {sheet}. Found: {list(df.columns[:3])}")
                continue

            temp = df[[date_col, val_col]].copy()
            temp.columns = ['date', var_name]
            
            # Convert to datetime and clean
            temp['date'] = pd.to_datetime(temp['date'])
            temp = temp.dropna(subset=['date'])
            
            # Merge logic
            if final_df.empty:
                final_df = temp
            else:
                final_df = pd.merge(final_df, temp, on='date', how='outer')
                
            print(f"✅ {sheet} processed: {len(temp)} rows found.")
                
        except Exception as e:
            print(f"⚠️  Failed to process sheet {sheet}: {e}")

    # 4. FINALIZATION
    if final_df.empty:
        print("❌ ERROR: No data was extracted. check sheet names and column headers.")
        return

    # Sort by date and save
    final_df.sort_values('date', inplace=True)
    final_df.to_csv(output_csv, index=False)
    
    print(f"\n✨ SUCCESS: Merged data saved to {output_csv}")
    print(f"📊 Final Shape: {final_df.shape}")

if __name__ == "__main__":
    fetch_and_verify_macro_data()