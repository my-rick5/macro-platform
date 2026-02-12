import pandas as pd
import os
import shutil
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #687 Target-F0 Hunter)... ")
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"❌ FATAL: Could not load Excel file: {e}")
        return

    mapping = {'unemp': 'adjlegrt', 'lur': 'adjlegrt', 'gdp': 'anngr', 'pce': 'eco'}
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in mapping: continue 
            
        var_name = mapping[s_clean]
        try:
            df = pd.read_excel(xls, sheet_name=sheet)
            
            # --- THE "GREENBOOK" TARGETING LOGIC ---
            # We want 'F0' (the current quarter forecast/estimate)
            # We explicitly EXCLUDE 'GBDATE'
            target_col = None
            for c in df.columns:
                c_str = str(c).upper()
                if 'GBDATE' in c_str: continue # Explicitly skip the junk column
                
                # Priority 1: Exact match for F0 (e.g., UNEMPF0)
                if 'F0' in c_str:
                    target_col = c
                    break
            
            # Fallback: If no F0, take the first column that isn't the date
            if not target_col:
                target_col = df.columns[1]

            print(f"   🎯 TARGETED Winner for '{sheet}': '{target_col}'")
            
            # Process the data
            processed_df = pd.DataFrame({
                'date_raw': df.iloc[:, 0],
                var_name: pd.to_numeric(df[target_col], errors='coerce')
            }).dropna()

            # Quarterly Date Parsing
            def parse_period(val):
                try:
                    f_val = float(val)
                    year, rem = int(f_val), f_val - int(f_val)
                    q = 1 if rem < 0.1 else 2 if rem < 0.3 else 3 if rem < 0.6 else 4
                    return f"{year}Q{q}"
                except: return None

            processed_df['date'] = processed_df['date_raw'].apply(parse_period)
            final_df = processed_df.dropna(subset=['date', var_name]).groupby('date')[var_name].last().reset_index()
            
            final_df.to_csv(os.path.join(output_dir, f"{var_name}.csv"), index=False)
            print(f"   ✅ SUCCESS: Saved {var_name}.csv")
                
        except Exception as e:
            print(f"   ❌ Error processing sheet '{sheet}': {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')