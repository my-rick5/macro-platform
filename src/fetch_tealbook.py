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
    # Ensure we look for all three variables
    target_mapping = {
        'unemp_x': ['UNEMP'], 
        'gdp_growth_x': ['gRGDP'], 
        'pce_inf_x': ['gPPCE']
    }
    
    final_df = pd.DataFrame()

    for var_name, search_sheets in target_mapping.items():
        sheet = next((s for s in xl.sheet_names if s.upper() in search_sheets), None)
        if not sheet: continue

        df = pd.read_excel(xl, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        
        date_col = next((c for c in df.columns if c.upper() == 'DATE'), None)
        # Try to find a quarter column if it exists
        q_col = next((c for c in df.columns if c.upper() in ['QUARTER', 'PER', 'QTR']), None)
        val_col = next((c for c in df.columns if c.upper().endswith('B4')), df.columns[1])

        temp = df.copy()

        def convert_to_quarterly(row):
            try:
                raw_val = float(row[date_col])
                # Case 1: Decimal format (2015.1, 2015.2...)
                if 1900 < raw_val < 2100:
                    year = int(raw_val)
                    # Extract decimal part for quarter
                    frac = round(raw_val - year, 2)
                    month = '01' # Default Q1
                    if q_col:
                        q = int(row[q_col])
                        month = {1:'01', 2:'04', 3:'07', 4:'10'}.get(q, '01')
                    elif frac == 0.25 or frac == 0.1: month = '04' # Q2
                    elif frac == 0.50 or frac == 0.2: month = '07' # Q3
                    elif frac == 0.75 or frac == 0.3: month = '10' # Q4
                    
                    return pd.to_datetime(f"{year}-{month}-01")
            except:
                pass
            return pd.to_datetime(row[date_col], errors='coerce')

        temp['date'] = temp.apply(convert_to_quarterly, axis=1)
        temp = temp[['date', val_col]].rename(columns={val_col: var_name}).dropna()
        temp = temp.sort_values('date').drop_duplicates('date', keep='last')

        if final_df.empty:
            final_df = temp
        else:
            # Use 'outer' merge to ensure we don't lose columns if dates don't align
            final_df = pd.merge(final_df, temp, on='date', how='outer')

    if not final_df.empty:
        final_df = final_df.sort_values('date')
        final_df.to_csv(output_csv, index=False)
        print(f"✨ SUCCESS: Merged {len(final_df)} rows. Columns: {list(final_df.columns)}")