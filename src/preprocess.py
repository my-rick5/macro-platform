import pandas as pd
import os
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #661 Magnitude Guard)... ")
    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    
    mapping = {'unemp': 'adjlegrt', 'lur': 'adjlegrt', 'gdp': 'anngr', 'anngr': 'anngr'}
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in mapping: continue 
            
        var_name = mapping[s_clean]
        try:
            df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
            df.rename(columns={df.columns[0]: 'date_raw'}, inplace=True)
            
            # --- UPDATED HUNTER LOGIC ---
            data_col = None
            for c in df.columns:
                if c == 'date_raw': continue
                converted = pd.to_numeric(df[c], errors='coerce')
                
                # Magnitude Guard: Dates (YYYYMMDD) are usually > 19000000.
                # Unemployment and GDP residuals should be < 1000.
                if converted.notna().sum() > 5 and converted.abs().max() < 1000:
                    df[var_name] = converted
                    data_col = c
                    print(f"   🎯 Valid economic data found in column: '{c}'")
                    break
            
            if not data_col:
                print(f"   ⚠️ WARNING: Could not find valid economic data in '{sheet}'")
                continue

            # Decimal Date Parsing
            def parse_period(val):
                try:
                    f_val = float(val)
                    year, rem = int(f_val), f_val - int(f_val)
                    q = 1 if rem < 0.1 else 2 if rem < 0.3 else 3 if rem < 0.6 else 4
                    return f"{year}Q{q}"
                except: return None

            df['date'] = df['date_raw'].apply(parse_period)
            
            # Collapse duplicates and save
            final_df = df.dropna(subset=['date', var_name])
            if not final_df.empty:
                final_df = final_df.groupby('date')[var_name].last().reset_index()
                final_df.to_csv(os.path.join(output_dir, f"{var_name}.csv"), index=False)
                print(f"   ✅ Saved deduplicated series: {var_name}")
                
        except Exception as e:
            print(f"   ❌ Error in {sheet}: {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')