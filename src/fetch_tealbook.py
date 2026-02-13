import os
import pandas as pd
import numpy as np

def fetch_and_verify_macro_data():
    base_dir = "/home/spark"
    local_xlsx = os.path.join(base_dir, "library.xlsx")
    data_dir = os.path.join(base_dir, "data")
    output_csv = os.path.join(data_dir, "tealbook_full_x.csv")
    os.makedirs(data_dir, exist_ok=True)

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
            print(f"❌ Error: Sheet for {var_name} not found in {all_sheets}")
            continue

        df = pd.read_excel(xl, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identify columns
        date_col = next((c for c in df.columns if c.upper() == 'DATE'), None)
        # B4 represents the historical data in Philly Fed's Greenbook sets
        val_col = next((c for c in df.columns if c.upper().endswith('B4')), df.columns[1])

        temp = df[[date_col, val_col]].copy()
        
        def robust_quarter_parser(val):
            try:
                raw = float(val)
                year = int(raw)
                frac = round(raw - year, 2)
                # Range-based matching handles floating point rounding errors (e.g., 2018.25 vs 2018.2)
                if frac < 0.2: month = '01'      # Q1 (.0 or .1)
                elif frac < 0.4: month = '04'    # Q2 (.2 or .25)
                elif frac < 0.6: month = '07'    # Q3 (.3 or .50)
                else: month = '10'               # Q4 (.4 or .75)
                return pd.to_datetime(f"{year}-{month}-01")
            except:
                return pd.to_datetime(val, errors='coerce')

        temp['date'] = temp[date_col].apply(robust_quarter_parser)
        temp = temp[['date', val_col]].rename(columns={val_col: var_name}).dropna()
        temp = temp.sort_values('date').drop_duplicates('date', keep='last')

        if final_df.empty:
            final_df = temp
        else:
            # OUTER merge ensures we keep all dates across all variables
            final_df = pd.merge(final_df, temp, on='date', how='outer')

    if not final_df.empty:
        # Sort and fill any missing data holes (forward fill)
        final_df = final_df.sort_values('date').ffill().bfill().reset_index(drop=True)
        final_df.to_csv(output_csv, index=False)
        print(f"✨ SUCCESS: Merged {len(final_df)} rows. Columns: {list(final_df.columns)}")
    else:
        print("❌ CRITICAL: No data was merged. Check if 'library.xlsx' is empty.")

if __name__ == "__main__":
    fetch_and_verify_macro_data()