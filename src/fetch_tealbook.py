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
    available_sheets = xl.sheet_names
    
    target_mapping = {
        'unemp_x': ['UNEMP', 'unemp'],
        'gdp_growth_x': ['gRGDP', 'grgdp'],
        'pce_inf_x': ['gPPCE', 'gppce']
    }

    final_df = pd.DataFrame()

    for var_name, possible_sheets in target_mapping.items():
        sheet = next((s for s in possible_sheets if s in available_sheets), None)
        if not sheet: continue

        try:
            df = pd.read_excel(xl, sheet_name=sheet)
            df.columns = [str(c).strip() for c in df.columns]
            
            date_col = next((c for c in df.columns if c.upper() == 'DATE'), None)
            val_col = next((c for c in df.columns if c != date_col), None)

            if date_col and val_col:
                temp = df[[date_col, val_col]].copy()
                temp.columns = ['date', var_name]
                
                # --- FIX: SMART DATE CONVERSION ---
                # Check if the column is just years (like 2015, 2016)
                first_val = temp['date'].iloc[0]
                if isinstance(first_val, (int, float, np.integer)) and 1900 < first_val < 2100:
                    # Convert integer year to Jan 1st of that year
                    temp['date'] = pd.to_datetime(temp['date'].astype(int).astype(str) + '-01-01')
                else:
                    # Standard parsing for actual date objects
                    temp['date'] = pd.to_datetime(temp['date'], errors='coerce')
                
                temp = temp.dropna(subset=['date'])
                
                # Deduplicate and merge
                temp = temp.sort_values('date').drop_duplicates('date', keep='last')
                
                if final_df.empty:
                    final_df = temp
                else:
                    final_df = pd.merge(final_df, temp, on='date', how='outer')
                
                print(f"✅ {sheet} parsed. Sample date: {temp['date'].iloc[-1].year}")

        except Exception as e:
            print(f"❌ Failed {sheet}: {e}")

    if not final_df.empty:
        final_df.sort_values('date', inplace=True)
        # Drop rows where everything is NaN (to clean up the 1970 artifacts)
        final_df = final_df.dropna(subset=['unemp_x', 'gdp_growth_x', 'pce_inf_x'], how='all')
        final_df.to_csv(output_csv, index=False)
        print(f"✨ Success: Data merged. Final rows: {len(final_df)}")

if __name__ == "__main__":
    fetch_and_verify_macro_data()