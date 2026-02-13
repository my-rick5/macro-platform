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
    
    # Mapping to ensure we hit all three required variables
    target_mapping = {
        'unemp_x': ['UNEMP'], 
        'gdp_growth_x': ['gRGDP'], 
        'pce_inf_x': ['gPPCE']
    }
    
    # Start with an empty DataFrame that we will merge everything into
    final_df = pd.DataFrame()

    for var_name, search_sheets in target_mapping.items():
        sheet = next((s for s in xl.sheet_names if s.upper() in search_sheets), None)
        if not sheet: 
            print(f"⚠️ Warning: Could not find sheet for {var_name}")
            continue

        df = pd.read_excel(xl, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        
        # 1. Identity Columns
        date_col = next((c for c in df.columns if c.upper() == 'DATE'), None)
        val_col = next((c for c in df.columns if c.upper().endswith('B4')), df.columns[1])

        # 2. Extract and Parse Dates (Handling decimal quarters like 2015.1, 2015.2)
        temp = df[[date_col, val_col]].copy()
        
        def robust_quarter_parser(val):
            try:
                raw = float(val)
                year = int(raw)
                frac = round(raw - year, 2)
                # Map decimal quarters to standard months
                month = '01' # Default Q1 (.0 or .1)
                if frac in [0.2, 0.25]: month = '04' # Q2
                elif frac in [0.5, 0.50]: month = '07' # Q3
                elif frac in [0.7, 0.75]: month = '10' # Q4
                return pd.to_datetime(f"{year}-{month}-01")
            except:
                return pd.to_datetime(val, errors='coerce')

        temp['date'] = temp[date_col].apply(robust_quarter_parser)
        
        # 3. Clean and Merge
        temp = temp[['date', val_col]].rename(columns={val_col: var_name}).dropna()
        temp = temp.sort_values('date').drop_duplicates('date', keep='last')

        if final_df.empty:
            final_df = temp
        else:
            # Use OUTER merge to prevent dropping columns if dates don't align perfectly
            final_df = pd.merge(final_df, temp, on='date', how='outer')

    # Final cleanup: Sort and save
    if not final_df.empty:
        final_df = final_df.sort_values('date').reset_index(drop=True)
        final_df.to_csv(output_csv, index=False)
        print(f"✨ SUCCESS: Merged {len(final_df)} rows. Columns: {list(final_df.columns)}")
    else:
        print("❌ CRITICAL: Final merge resulted in an empty dataset.")