import pandas as pd
import os
import shutil

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #700 Strict Exclusion)... ")
    
    # 1. CLEAN SWEEP
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"❌ FATAL: Could not load Excel file: {e}")
        return

    # Map variables to their specific Greenbook headers
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

            # --- THE GBDATE PURGE ---
            # Drop any column that contains 'GBdate' (case-insensitive)
            cols_to_drop = [c for c in df.columns if 'gbdate' in str(c).lower()]
            if cols_to_drop:
                df.drop(columns=cols_to_drop, inplace=True)
                print(f"   🗑️ Purged metadata columns: {cols_to_drop}")

            if target_header not in df.columns:
                print(f"   ⚠️ Skipping '{sheet}': Header '{target_header}' not found.")
                continue

            # --- DEDUPLICATION ---
            temp_df = pd.DataFrame({
                'raw_date': df.iloc[:, 0],
                'value': pd.to_numeric(df[target_header], errors='coerce')
            }).dropna()

            def parse_period(val):
                try:
                    f_val = float(val)
                    year, rem = int(f_val), f_val - int(f_val)
                    q = 1 if rem < 0.15 else 2 if rem < 0.4 else 3 if rem < 0.65 else 4
                    return f"{year}Q{q}"
                except: return None

            temp_df['date'] = temp_df['raw_date'].apply(parse_period)
            
            # Collapsing multiple vintages to the last (most recent) entry
            final_df = temp_df.dropna(subset=['date']).groupby('date').last().reset_index()
            final_df = final_df[['date', 'value']].rename(columns={'value': var_name})

            final_df.to_csv(os.path.join(output_dir, f"{var_name}.csv"), index=False)
            print(f"   ✅ SUCCESS: Saved {var_name}.csv using {target_header}")
                
        except Exception as e:
            print(f"   ❌ Error processing sheet '{sheet}': {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')