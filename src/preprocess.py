import pandas as pd
import os
import shutil

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #695 Strict Targeting)... ")
    
    # 1. CLEAN SWEEP
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"❌ FATAL: Could not load Excel file: {e}")
        return

    # EXACT HEADER MAPPING (No more guessing)
    # Update these strings if your Excel headers use different codes
    strict_targets = {
        'unemp': 'UNEMPF0',
        'lur':   'UNEMPF0',
        'gdp':   'REALGDPF0',
        'pce':   'PCEF0'
    }
    
    mapping = {'unemp': 'adjlegrt', 'lur': 'adjlegrt', 'gdp': 'anngr', 'pce': 'eco'}
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in strict_targets: continue 
            
        target_header = strict_targets[s_clean]
        var_name = mapping[s_clean]
        
        try:
            df = pd.read_excel(xls, sheet_name=sheet)
            
            # STRICT CHECK: Does the targeted header actually exist?
            if target_header not in df.columns:
                print(f"   ❌ ERROR: Header '{target_header}' not found in '{sheet}'.")
                print(f"      Available columns: {list(df.columns[:5])}...") 
                continue

            print(f"   🎯 TARGETED: Using '{target_header}' for {var_name}")
            
            processed_df = pd.DataFrame({
                'date_raw': df.iloc[:, 0],
                var_name: pd.to_numeric(df[target_header], errors='coerce')
            }).dropna()

            # Date Parsing
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