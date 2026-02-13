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

    # Mapping based on common Philly Fed Row Format names
    target_mapping = {
        'unemp_x': ['UNEMP', 'unemp', 'RUC', 'RUnemp', 'unrate'], 
        'gdp_growth_x': ['gRGDP', 'grgdp', 'GDP', 'gdp'], 
        'pce_inf_x': ['gPPCE', 'gppce', 'PCE', 'pce']
    }
    
    final_df = pd.DataFrame()

    for var_name, possible_names in target_mapping.items():
        # Find the sheet regardless of case
        sheet = next((s for s in xl.sheet_names if s.upper() in [p.upper() for p in possible_names]), None)
        
        if not sheet:
            print(f"⚠️  {var_name}: No match found in sheets.")
            continue

        try:
            df = pd.read_excel(xl, sheet_name=sheet)
            df.columns = [str(c).strip() for c in df.columns]
            
            # 1. Identify DATE/YEAR column
            date_col = next((c for c in df.columns if c.upper() in ['DATE', 'YEAR']), None)
            
            # 2. Identify QUARTER/PERIOD column
            q_col = next((c for c in df.columns if c.upper() in ['QUARTER', 'PER', 'QTR', 'Q']), None)
            
            # 3. Identify VALUE column (Look for 'B4' suffix first, else grab the first non-date column)
            val_col = next((c for c in df.columns if c.upper().endswith('B4')), None)
            if not val_col:
                val_col = [c for c in df.columns if c not in [date_col, q_col]][0]

            print(f"✅ {sheet} -> date: {date_col}, q: {q_col}, val: {val_col}")
            
            # Build clean temp frame
            temp = df[[date_col, q_col, val_col]].copy()
            
            # Handle Quarter mapping (Q1=Jan, Q2=Apr, etc.)
            temp['month'] = temp[q_col].astype(float).astype(int).map({1: '01', 2: '04', 3: '07', 4: '10'})
            temp['date_str'] = temp[date_col].astype(int).astype(str) + "-" + temp['month'] + "-01"
            temp['date'] = pd.to_datetime(temp['date_str'], errors='coerce')
            
            # Keep only standard columns and deduplicate
            temp = temp[['date', val_col]].rename(columns={val_col: var_name}).dropna()
            temp = temp.sort_values('date').drop_duplicates('date', keep='last')

            if final_df.empty:
                final_df = temp
            else:
                final_df = pd.merge(final_df, temp, on='date', how='outer')

        except Exception as e:
            print(f"❌ Error on sheet {sheet}: {e}")

    # Final verification and save
    if not final_df.empty:
        final_df.sort_values('date', inplace=True)
        final_df.to_csv(output_csv, index=False)
        print(f"✨ SUCCESS: Merged {len(final_df)} quarterly rows.")
    else:
        print("❌ CRITICAL: No data was merged. Pipeline will stop.")