import os
import pandas as pd

def fetch_and_verify_macro_data():
    local_xlsx = "library.xlsx" 
    output_csv = "data/tealbook_full_x.csv"
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(local_xlsx):
        print(f"❌ ERROR: Source file not found at {os.path.abspath(local_xlsx)}")
        return

    # --- DISCOVERY PHASE ---
    # We load the workbook metadata once to see what we are dealing with
    xl = pd.ExcelFile(local_xlsx)
    available_sheets = xl.sheet_names
    print(f"📋 Workbook Sheets Found: {available_sheets}")

    # Standard Philly Fed sheet names for Row Format
    # Mapping our internal engine names to possible Excel sheet names
    target_mapping = {
        'unemp_x': ['UNEMP', 'unemp', 'RUC'],
        'gdp_growth_x': ['gRGDP', 'grgdp'],
        'pce_inf_x': ['gPPCE', 'gppce']
    }

    final_df = pd.DataFrame()

    for var_name, possible_sheets in target_mapping.items():
        # Find the first match that exists in the workbook
        sheet = next((s for s in possible_sheets if s in available_sheets), None)
        
        if not sheet:
            print(f"⚠️  Skipping {var_name}: None of {possible_sheets} found in workbook.")
            continue

        try:
            # Read the sheet
            df = pd.read_excel(xl, sheet_name=sheet)
            
            # Clean column names (strip whitespace and uppercase for matching)
            df.columns = [str(c).strip() for c in df.columns]
            
            # 1. Identify Date Column (usually 'DATE')
            date_col = next((c for c in df.columns if c.upper() == 'DATE'), None)
            
            # 2. Identify Value Column 
            # In Row Format, the first data column after 'DATE' is usually the 'B4' (history) 
            # or 'Q0' (nowcast). We take the first non-date column.
            val_col = next((c for c in df.columns if c != date_col), None)

            if date_col and val_col:
                print(f"✅ Processing {sheet}: Using '{date_col}' and '{val_col}'")
                temp = df[[date_col, val_col]].copy()
                temp.columns = ['date', var_name]
                
                # Convert to standard datetime
                temp['date'] = pd.to_datetime(temp['date'], errors='coerce')
                temp = temp.dropna(subset=['date'])
                
                if final_df.empty:
                    final_df = temp
                else:
                    final_df = pd.merge(final_df, temp, on='date', how='outer')
            else:
                print(f"⚠️  Sheet {sheet} structure invalid. Cols: {list(df.columns)}")

        except Exception as e:
            print(f"❌ Failed to process sheet {sheet}: {e}")

    # --- FINALIZATION ---
    if final_df.empty:
        print("❌ CRITICAL: No data extracted from any sheets.")
        return

    # Ensure chronological order
    final_df.sort_values('date', inplace=True)
    final_df.to_csv(output_csv, index=False)
    
    print(f"\n✨ SUCCESS: {len(final_df)} rows merged into {output_csv}")

if __name__ == "__main__":
    fetch_and_verify_macro_data()