import os
import pandas as pd
import numpy as np

def fetch_and_verify_macro_data():
    # 1. Setup paths for Docker environment
    base_dir = "/home/spark"
    local_xlsx = os.path.join(base_dir, "library.xlsx")
    data_dir = os.path.join(base_dir, "data")
    output_csv = os.path.join(data_dir, "tealbook_full_x.csv")
    os.makedirs(data_dir, exist_ok=True)

    if not os.path.exists(local_xlsx):
        print(f"❌ ERROR: Source file not found at {local_xlsx}")
        return

    # 2. Sheet Discovery
    xl = pd.ExcelFile(local_xlsx)
    all_sheets = xl.sheet_names
    print(f"📋 Found Sheets: {all_sheets}")

    # Mapping based on Philly Fed's standard worksheet names
    target_mapping = {
        'unemp_x': ['UNEMP', 'unemp'], 
        'gdp_growth_x': ['gRGDP', 'grgdp'], 
        'pce_inf_x': ['gPPCE', 'gppce']
    }
    
    final_df = pd.DataFrame()

    for var_name, search_keys in target_mapping.items():
        # Case-insensitive sheet discovery
        sheet = next((s for s in all_sheets if s.upper() in [k.upper() for k in search_keys]), None)
        
        if not sheet: 
            print(f"❌ Error: Sheet for {var_name} not found.")
            continue

        try:
            df = pd.read_excel(xl, sheet_name=sheet)
            df.columns = [str(c).strip() for c in df.columns]
            
            # Identify columns
            date_col = next((c for c in df.columns if c.upper() == 'DATE'), None)
            val_col = next((c for c in df.columns if c.upper().endswith('B4')), df.columns[1])

            temp = df[[date_col, val_col]].copy()
            
            # 3. FUZZY DECIMAL PARSER: Captures Q3/Q4 and handles float rounding
            def robust_quarter_parser(val):
                try:
                    raw = float(val)
                    year = int(raw)
                    frac = round(raw - year, 3) 
                    
                    # Handles both .1/.2/.3/.4 and .0/.25/.50/.75 conventions
                    if frac <= 0.15: 
                        month = '01' # Q1
                    elif 0.16 <= frac <= 0.35: 
                        month = '04' # Q2
                    elif 0.36 <= frac <= 0.60: 
                        month = '07' # Q3
                    else: 
                        month = '10' # Q4
                    
                    return pd.to_datetime(f"{year}-{month}-01")
                except:
                    # Fallback for standard date objects
                    return pd.to_datetime(val, errors='coerce')

            temp['date'] = temp[date_col].apply(robust_quarter_parser)
            
            # 4. Clean and Prepare for Merge
            temp = temp[['date', val_col]].rename(columns={val_col: var_name}).dropna()
            temp = temp.sort_values('date').drop_duplicates('date', keep='last')

            if final_df.empty:
                final_df = temp
            else:
                # OUTER merge ensures we keep all dates across all variables
                final_df = pd.merge(final_df, temp, on='date', how='outer')

        except Exception as e:
            print(f"⚠️ Error processing {sheet}: {e}")

    # 5. Final Alignment and Saving
    if not final_df.empty:
        # Sort and fill holes to ensure continuous time-series
        final_df = final_df.sort_values('date').ffill().bfill().reset_index(drop=True)
        final_df.to_csv(output_csv, index=False)
        
        print(f"✨ SUCCESS: Merged {len(final_df)} rows.")
        print(f"📊 Columns: {list(final_df.columns)}")
        
        # 6. Historical Diagnostic Print
        print("\n📜 HISTORICAL DATA SNAPSHOT (First 10 Rows):")
        print(final_df.head(10).to_string())
    else:
        print("❌ CRITICAL: No data was merged.")

if __name__ == "__main__":
    fetch_and_verify_macro_data()