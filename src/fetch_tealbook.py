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

    for var_name, sheets in target_mapping.items():
        sheet = next((s for s in xl.sheet_names if s.upper() in sheets), None)
        if not sheet: continue

        df = pd.read_excel(xl, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        date_col = next((c for c in df.columns if c.upper() == 'DATE'), None)
        val_col = next((c for c in df.columns if c.upper().endswith('B4')), df.columns[1])

        temp = df[[date_col, val_col]].copy()

        # --- THE FIX: FORCED YEAR PARSING ---
        def parse_philly_date(val):
            try:
                # If it's a raw year (e.g., 2015 or 2015.0)
                float_val = float(val)
                if 1900 < float_val < 2100:
                    return pd.to_datetime(f"{int(float_val)}-01-01")
            except:
                pass
            # Fallback for actual date objects
            return pd.to_datetime(val, errors='coerce')

        temp['date'] = temp[date_col].apply(parse_philly_date)
        
        # Clean up and merge
        temp = temp[['date', val_col]].rename(columns={val_col: var_name}).dropna()
        temp = temp.sort_values('date').drop_duplicates('date', keep='last')

        if final_df.empty:
            final_df = temp
        else:
            final_df = pd.merge(final_df, temp, on='date', how='outer')

    if not final_df.empty:
        final_df.sort_values('date', inplace=True)
        final_df.to_csv(output_csv, index=False)
        print(f"✨ SUCCESS: Merged {len(final_df)} rows with clean dates.")