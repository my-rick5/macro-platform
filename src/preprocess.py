import pandas as pd
import os
import shutil
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #691 Baseline Diagnostic)... ")
    
    # 1. CLEAN SWEEP: Ensure the results directory is fresh
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"❌ FATAL: Could not load Excel file: {e}")
        return

    # Map sheets to internal variable names
    mapping = {'unemp': 'adjlegrt', 'lur': 'adjlegrt', 'gdp': 'anngr', 'pce': 'eco'}
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in mapping: continue 
            
        var_name = mapping[s_clean]
        try:
            # Read sheet without skipping rows to maintain index integrity
            df = pd.read_excel(xls, sheet_name=sheet)
            
            # --- TARGET F0 (NOWCAST) ---
            # We specifically want the "Current" forecast column, ignoring metadata like GBDATE
            target_col = None
            for c in df.columns:
                c_str = str(c).upper()
                if 'GBDATE' in c_str: continue 
                if 'F0' in c_str:
                    target_col = c
                    break
            
            # Fallback to first data column if F0 isn't explicitly found
            if not target_col:
                target_col = df.columns[1]

            # --- DATA EXTRACTION (UNSCALED) ---
            raw_series = pd.to_numeric(df[target_col], errors='coerce')
            
            # Log the mean to Jenkins console for diagnostic visibility
            raw_mean = raw_series.mean()
            print(f"   📊 Diagnostic: '{target_col}' mean is {raw_mean:.4f}")
            print(f"   🎯 FINAL Winner for '{sheet}': '{target_col}' (Unscaled)")
            
            processed_df = pd.DataFrame({
                'date_raw': df.iloc[:, 0],
                var_name: raw_series
            }).dropna()

            # --- QUARTERLY DATE PARSING ---
            def parse_period(val):
                try:
                    f_val = float(val)
                    year, rem = int(f_val), f_val - int(f_val)
                    # Maps Excel decimal dates (e.g., 2010.1) to quarters
                    q = 1 if rem < 0.1 else 2 if rem < 0.3 else 3 if rem < 0.6 else 4
                    return f"{year}Q{q}"
                except: return None

            processed_df['date'] = processed_df['date_raw'].apply(parse_period)
            
            # Deduplicate by taking the last entry for each quarter
            final_df = processed_df.dropna(subset=['date', var_name]).groupby('date')[var_name].last().reset_index()
            
            # Export to the processed directory for the engine to consume
            final_df.to_csv(os.path.join(output_dir, f"{var_name}.csv"), index=False)
            print(f"   ✅ SUCCESS: Saved {var_name}.csv")
                
        except Exception as e:
            print(f"   ❌ Error processing sheet '{sheet}': {e}")

if __name__ == "__main__":
    # Standard container paths
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')