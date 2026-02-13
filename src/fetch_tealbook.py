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
    
    # Mapping using 'contains' logic to be extremely aggressive
    target_mapping = {
        'unemp_x': ['UNEMP'], 
        'gdp_growth_x': ['GRGDP', 'GDPR'], 
        'pce_inf_x': ['GPCE', 'PPCE']
    }
    
    final_df = pd.DataFrame()

    for var_name, keys in target_mapping.items():
        # Find sheet where name CONTAINS any of our keys (case-insensitive)
        sheet = next((s for s in all_sheets if any(k.upper() in s.upper() for k in keys)), None)
        
        if not sheet: 
            print(f"⚠️ Warning: No sheet found for {var_name}")
            continue

        df = pd.read_excel(xl, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        
        date_col = next((c for c in df.columns if c.upper() == 'DATE'), None)
        val_col = next((c for c in df.columns if c.upper().endswith('B4')), df.columns[1])

        temp = df[[date_col, val_col]].copy()
        
        def robust_quarter_parser(val):
            try:
                raw = float(val)
                year = int(raw)
                frac = round(raw - year, 3) 
                # Widen ranges to catch .3, .4, .75, etc.
                if frac <= 0.15: month = '01'
                elif 0.16 <= frac <= 0.35: month = '04'
                elif 0.36 <= frac <= 0.65: month = '07' # Covers .4 and .5
                else: month = '10'                     # Covers .7 and .75
                return pd.to_datetime(f"{year}-{month}-01")
            except:
                return pd.to_datetime(val, errors='coerce')

        temp['date'] = temp[date_col].apply(robust_quarter_parser)
        temp = temp[['date', val_col]].rename(columns={val_col: var_name}).dropna()
        temp = temp.sort_values('date').drop_duplicates('date', keep='last')

        if final_df.empty:
            final_df = temp
        else:
            # OUTER merge is critical to prevent losing columns
            final_df = pd.merge(final_df, temp, on='date', how='outer')

    if not final_df.empty:
        final_df = final_df.sort_values('date').reset_index(drop=True)
        # Final safety: forward fill any small holes
        final_df = final_df.ffill().bfill()
        final_df.to_csv(output_csv, index=False)
        print(f"✨ SUCCESS: Merged {len(final_df)} rows. Columns: {list(final_df.columns)}")