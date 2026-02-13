import os
import pandas as pd
import numpy as np

def fetch_and_verify_macro_data():
    base_dir = "/home/spark"
    local_xlsx = os.path.join(base_dir, "library.xlsx")
    data_dir = os.path.join(base_dir, "data")
    output_csv = os.path.join(data_dir, "tealbook_full_x.csv")
    os.makedirs(data_dir, exist_ok=True)

    if not os.path.exists(local_xlsx):
        print(f"❌ ERROR: Source file not found at {local_xlsx}")
        return

    xl = pd.ExcelFile(local_xlsx)
    print(f"📋 Workbook Sheets Found: {xl.sheet_names}")

    target_mapping = {
        'unemp_x': ['UNEMP', 'unemp'], 
        'gdp_growth_x': ['gRGDP', 'grgdp'], 
        'pce_inf_x': ['gPPCE', 'gppce']
    }
    
    final_df = pd.DataFrame()

    for var_name, possible_names in target_mapping.items():
        sheet = next((s for s in xl.sheet_names if s.upper() in [p.upper() for p in possible_names]), None)
        if not sheet: continue

        try:
            df = pd.read_excel(xl, sheet_name=sheet)
            df.columns = [str(c).strip() for c in df.columns]
            
            date_col = next((c for c in df.columns if c.upper() in ['DATE', 'YEAR']), None)
            q_col = next((c for c in df.columns if c.upper() in ['QUARTER', 'PER', 'QTR']), None)
            val_col = next((c for c in df.columns if c.upper().endswith('B4')), df.columns[1])

            # --- DYNAMIC COLUMN SELECTION ---
            cols_to_grab = [date_col, val_col]
            if q_col:
                cols_to_grab.insert(1, q_col)
            
            temp = df[cols_to_grab].copy()

            # --- DATE RECONSTRUCTION ---
            if q_col:
                # Use Quarter + Year logic
                temp['month'] = temp[q_col].astype(float).astype(int).map({1: '01', 2: '04', 3: '07', 4: '10'})
                temp['date_str'] = temp[date_col].astype(int).astype(str) + "-" + temp['month'] + "-01"
                temp['date'] = pd.to_datetime(temp['date_str'], errors='coerce')
            else:
                # Fallback: Parse the DATE column directly if it's already a date/float
                # Philly Fed dates are often YYYY.Q (e.g., 2015.1)
                temp['date'] = pd.to_datetime(temp[date_col], errors='coerce')

            temp = temp[['date', val_col]].rename(columns={val_col: var_name}).dropna()
            temp = temp.sort_values('date').drop_duplicates('date', keep='last')

            if final_df.empty:
                final_df = temp
            else:
                final_df = pd.merge(final_df, temp, on='date', how='outer')
            
            print(f"✅ {sheet} -> Processed {len(temp)} rows.")

        except Exception as e:
            print(f"❌ Error on sheet {sheet}: {e}")

    if not final_df.empty:
        final_df.sort_values('date', inplace=True)
        final_df.to_csv(output_csv, index=False)
        print(f"✨ SUCCESS: Merged {len(final_df)} quarterly rows.")
    else:
        print("❌ CRITICAL: No data was merged.")

if __name__ == "__main__":
    fetch_and_verify_macro_data()