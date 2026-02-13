import os
import pandas as pd

def fetch_and_verify_macro_data():
    data_dir = "/home/spark/data"
    local_xlsx = os.path.join(data_dir, "library.xlsx") 
    output_csv = os.path.join(data_dir, "data", "tealbook_full_x.csv")
    
    # Ensure the directory exists
    os.makedirs(data_dir, exist_ok=True)

    # 🛑 CHECK 1: Does the source file actually exist?
    if not os.path.exists(local_xlsx):
        print(f"❌ ERROR: Source file not found at {local_xlsx}")
        print("Check if your Dockerfile COPY or your download logic is working.")
        return # Exit early so we don't hit the KeyError later

    sheet_map = {
        'unemp_x': 'RUC',      
        'gdp_growth_x': 'gRGDP', 
        'pce_inf_x': 'gPPCE'    
    }

    final_df = pd.DataFrame()
    print("🔍 Beginning data extraction and verification...")

    for var_name, sheet in sheet_map.items():
        try:
            df = pd.read_excel(local_xlsx, sheet_name=sheet, engine='openpyxl')
            
            # --- DEBUGGING: List columns if 'Date of Meeting' is missing ---
            if 'Date of Meeting' not in df.columns:
                print(f"⚠️  Sheet {sheet} columns: {list(df.columns)}")
                continue

            temp = df[['Date of Meeting', 'Q0']].copy()
            temp.columns = ['date', var_name]
            
            sample_val = temp[var_name].dropna().iloc[-1]
            if sample_val > 50: 
                print(f"❌ ERROR: {var_name} appears to be a date index ({sample_val})")
            else:
                print(f"✅ {var_name} verified. Sample: {sample_val}%")

            temp['date'] = pd.to_datetime(temp['date'])
            
            if final_df.empty:
                final_df = temp
            else:
                final_df = pd.merge(final_df, temp, on='date', how='outer')
                
        except Exception as e:
            print(f"⚠️  Failed to process sheet {sheet}: {e}")

    # 🛑 CHECK 2: Safety Gate before sorting
    if final_df.empty:
        print("❌ ERROR: No data was extracted from any sheets. Abortion sorting.")
        return

    final_df.sort_values('date', inplace=True)
    final_df.to_csv(output_csv, index=False)
    print(f"\n✨ Successfully merged {len(final_df)} quarters of data into {output_csv}")