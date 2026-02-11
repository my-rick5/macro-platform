import pandas as pd
import os
import shutil
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #680 Non-Numeric Hunter)... ")
    
    # 1. CLEAN SWEEP: Force-delete old data to prevent stale results
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"❌ FATAL: Could not load Excel file: {e}")
        return

    mapping = {
        'unemp': 'adjlegrt', 
        'lur': 'adjlegrt', 
        'gdp': 'anngr', 
        'anngr': 'anngr', 
        'pce': 'eco'
    }
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in mapping: 
            continue 
            
        var_name = mapping[s_clean]
        try:
            df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
            df.rename(columns={df.columns[0]: 'date_raw'}, inplace=True)
            
            candidates = []
            for c in df.columns:
                if c == 'date_raw': continue
                
                # Normalize header to string for pattern matching
                c_str = str(c).lower().strip()
                
                # --- NEW: NON-NUMERIC HEADER FILTER ---
                # Rejects headers that are just numbers or version decimals (e.g., '3.7', '2024')
                if re.match(r'^[0-9.]+$', c_str): continue
                
                # --- INTEGRITY GUARD ---
                # Rejects empty, 'nan', or generic pandas 'unnamed' headers
                if not c_str or c_str == 'nan' or 'unnamed' in c_str: continue
                
                converted = pd.to_numeric(df[c], errors='coerce')
                valid_count = converted.notna().sum()
                
                # --- DATA VALIDATION (Density + Mean Range) ---
                if valid_count > 150:
                    avg_val = converted.mean()
                    # Rejects extreme values (like dates/IDs) by checking if mean is macro-realistic
                    if not (-10 < avg_val < 25): continue
                    
                    # --- SCORING (Macro Keyword Match) ---
                    keywords = ['rate', 'unemp', 'lur', 'val', 'adj', 'index', var_name]
                    has_keyword = any(k in c_str for k in keywords)
                    
                    score = (100 if has_keyword else 10)
                    candidates.append({'col': c, 'data': converted, 'score': score, 'count': valid_count})
            
            if candidates:
                # Prioritize by Keyword Score first, then Data Density (Count)
                winner = sorted(candidates, key=lambda x: (x['score'], x['count']), reverse=True)[0]
                df[var_name] = winner['data']
                print(f"   🎯 FINAL Winner for '{sheet}': '{winner['col']}' ({winner['count']} pts)")
            else:
                print(f"   ⚠️ WARNING: No valid labeled macro series found in '{sheet}'.")
                continue

            # --- QUARTERLY DATE PARSING ---
            def parse_period(val):
                try:
                    f_val = float(val)
                    year, rem = int(f_val), f_val - int(f_val)
                    # Maps decimal remainders to standard Q1-Q4 buckets
                    q = 1 if rem < 0.1 else 2 if rem < 0.3 else 3 if rem < 0.6 else 4
                    return f"{year}Q{q}"
                except: return None

            df['date'] = df['date_raw'].apply(parse_period)
            
            # --- DEDUPLICATION & EXPORT ---
            final_df = df.dropna(subset=['date', var_name])
            if not final_df.empty:
                final_df = final_df.groupby('date')[var_name].last().reset_index()
                final_df.to_csv(os.path.join(output_dir, f"{var_name}.csv"), index=False)
                print(f"   ✅ SUCCESS: Saved {var_name}.csv")
                
        except Exception as e:
            print(f"   ❌ Error processing sheet '{sheet}': {e}")

if __name__ == "__main__":
    # Standard paths used in the Calibration Engine Docker environment
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')