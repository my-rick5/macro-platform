import os
import pandas as pd
import numpy as np

def fetch_and_verify_macro_data():
    local_xlsx = "library.xlsx" 
    output_csv = "data/tealbook_full_x.csv"
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(local_xlsx):
        print(f"❌ ERROR: Source file not found.")
        return

    xl = pd.ExcelFile(local_xlsx)
    
    target_mapping = {
        'unemp_x': ['UNEMP', 'unemp'],
        'gdp_growth_x': ['gRGDP', 'grgdp'],
        'pce_inf_x': ['gPPCE', 'gppce']
    }

    final_df = pd.DataFrame()

    for var_name, possible_sheets in target_mapping.items():
        sheet = next((s for s in possible_sheets if s in xl.sheet_names), None)
        if not sheet: continue

        try:
            df = pd.read_excel(xl, sheet_name=sheet)
            df.columns = [str(c).strip() for c in df.columns]
            
            # 1. Identify Date and Value columns
            date_col = next((c for c in df.columns if c.upper() == 'DATE'), None)
            val_col = next((c for c in df.columns if c.upper().endswith('B4') or c.upper() == 'Q0'), df.columns[1])

            # 2. Identify a 'Quarter' column if it exists to prevent skipping
            q_col = next((c for c in df.columns if c.upper() in ['QUARTER', 'PER', 'QTR']), None)

            if date_col and val_col:
                temp = df[[date_col, val_col]].copy()
                if q_col:
                    # If we have a quarter column, create a more precise date string
                    temp['q_val'] = df[q_col].astype(str)
                    temp['date_str'] = temp[date_col].astype(str) + "-Q" + temp['q_val']
                else:
                    temp['date_str'] = temp[date_col].astype(str)

                temp.columns = ['raw_date', var_name, 'q_val', 'date_key'] if q_col else ['raw_date', var_name, 'date_key']
                
                # Deduplicate: Keep the most recent data for each unique date/quarter key
                temp = temp.sort_values('raw_date').drop_duplicates('date_key', keep='last')
                
                # Standardize the key for merging
                temp['date'] = pd.to_datetime(temp['date_key'], errors='coerce')
                temp = temp[['date', var_name]].dropna(subset=['date'])

                if final_df.empty:
                    final_df = temp
                else:
                    final_df = pd.merge(final_df, temp, on='date', how='outer')
                
                print(f"✅ {sheet} parsed. Found {len(temp)} unique periods.")

        except Exception as e:
            print(f"❌ Failed {sheet}: {e}")

    if not final_df.empty:
        final_df.sort_values('date', inplace=True)
        # Drop rows where we have no data at all
        final_df = final_df.dropna(subset=['unemp_x', 'gdp_growth_x', 'pce_inf_x'], how='all')
        final_df.to_csv(output_csv, index=False)
        print(f"✨ Success: Data merged. Final rows: {len(final_df)}")

if __name__ == "__main__":
    fetch_and_verify_macro_data()