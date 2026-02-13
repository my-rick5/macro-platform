import os
import pandas as pd

def fetch_and_verify_macro_data():
    local_xlsx = "library.xlsx" 
    output_csv = "data/tealbook_full_x.csv"
    os.makedirs("data", exist_ok=True)

    xl = pd.ExcelFile(local_xlsx)
    target_mapping = {'unemp_x': ['UNEMP'], 'gdp_growth_x': ['gRGDP'], 'pce_inf_x': ['gPPCE']}
    final_df = pd.DataFrame()

    for var_name, possible_sheets in target_mapping.items():
        sheet = next((s for s in possible_sheets if s in xl.sheet_names), None)
        if not sheet: continue

        df = pd.read_excel(xl, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        
        date_col = next((c for c in df.columns if c.upper() == 'DATE'), None)
        q_col = next((c for c in df.columns if c.upper() in ['QUARTER', 'PER', 'QTR']), None)
        val_col = next((c for c in df.columns if c.upper().endswith('B4')), df.columns[1])

        if date_col and q_col and val_col:
            temp = df[[date_col, q_col, val_col]].copy()
            
            # --- FIX: ALIGN QUARTERS TO STANDARD MONTHS ---
            # Q1 -> Jan (01), Q2 -> Apr (04), Q3 -> Jul (07), Q4 -> Oct (10)
            temp['month'] = temp[q_col].map({1: '01', 2: '04', 3: '07', 4: '10'})
            temp['date_str'] = temp[date_col].astype(int).astype(str) + "-" + temp['month'] + "-01"
            
            temp['date'] = pd.to_datetime(temp['date_str'], errors='coerce')
            temp = temp[['date', val_col]].rename(columns={val_col: var_name})
            
            # Deduplicate by date (keep latest vintage)
            temp = temp.sort_values('date').drop_duplicates('date', keep='last').dropna()

            if final_df.empty:
                final_df = temp
            else:
                final_df = pd.merge(final_df, temp, on='date', how='outer')

    if not final_df.empty:
        final_df.sort_values('date', inplace=True).to_csv(output_csv, index=False)
        print(f"✨ Success: Merged {len(final_df)} quarters.")

if __name__ == "__main__":
    fetch_and_verify_macro_data()