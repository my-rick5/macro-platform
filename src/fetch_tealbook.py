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
    target_mapping = {'unemp_x': ['UNEMP'], 'gdp_growth_x': ['gRGDP'], 'pce_inf_x': ['gPPCE']}
    final_df = pd.DataFrame()

    for var_name, search_keys in target_mapping.items():
        sheet = next((s for s in xl.sheet_names if s.upper() in search_keys), None)
        if not sheet: continue

        df = pd.read_excel(xl, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        date_col = next((c for c in df.columns if c.upper() == 'DATE'), None)
        val_col = next((c for c in df.columns if c.upper().endswith('B4')), df.columns[1])

        temp = df[[date_col, val_col]].copy()
        
        def robust_quarter_parser(val):
            try:
                raw = float(val)
                year = int(raw)
                # Extract the fractional part (e.g., .1, .2, .25, .3)
                frac = round(raw - year, 2)
                
                # PHILLY FED LOGIC: 
                # Q1 is .0 or .1
                # Q2 is .2 or .25
                # Q3 is .3 or .5
                # Q4 is .4 or .75
                if frac <= 0.15: month = '01'
                elif 0.16 <= frac <= 0.29: month = '04'
                elif 0.30 <= frac <= 0.60: month = '07'
                else: month = '10'
                
                return pd.to_datetime(f"{year}-{month}-01")
            except:
                return pd.to_datetime(val, errors='coerce')

        temp['date'] = temp[date_col].apply(robust_quarter_parser)
        temp = temp[['date', val_col]].rename(columns={val_col: var_name}).dropna()
        
        # Keep only the last vintage for each distinct quarter
        temp = temp.sort_values('date').drop_duplicates('date', keep='last')

        if final_df.empty:
            final_df = temp
        else:
            final_df = pd.merge(final_df, temp, on='date', how='outer')

    if not final_df.empty:
        # Final cleanup: ensure we have no gaps in the timeline
        final_df = final_df.sort_values('date').reset_index(drop=True)
        final_df.to_csv(output_csv, index=False)
        print(f"✨ SUCCESS: Merged {len(final_df)} rows. Columns: {list(final_df.columns)}")