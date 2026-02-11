import pandas as pd
import os
import shutil
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #681 Alpha-Enforced Hunter)... ")
    
    # 1. CLEAN SWEEP: Purge old artifacts to ensure fresh results
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
        if s_clean not in mapping: continue 
            
        var_name = mapping[s_clean]
        try:
            df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
            df.rename(columns={df.columns[0]: 'date_raw'}, inplace=True)
            
            candidates = []
            for c in df.columns:
                if c == 'date_raw': continue
                c_str = str(c).lower().strip()
                
                # --- ALPHA-ENFORCEMENT GUARD ---
                # Rejects headers that don't contain any letters (a-z).
                # This kills '3.7', 'nan', 'nan.1', and any numeric version tags.
                if not re.search(r'[a-z]', c_str): continue
                
                # --- INTEGRITY GUARD ---
                # Skip generic pandas "unnamed" labels
                if 'unnamed' in c_str: continue
                
                converted = pd.to_numeric(df[c], errors='coerce')
                valid_count = converted.notna().sum()
                
                # --- DATA VALIDATION ---
                if valid_count > 150:
                    avg_val = converted.mean()
                    # Rejects high-value IDs or dates; keeps realistic macro rates (-10 to 25)
                    if not (-10 < avg_val < 25): continue
                    
                    keywords = ['rate', 'unemp', 'lur', 'val', 'adj', 'index', var_name]
                    has_keyword = any(k in c_str for k in keywords)
                    
                    # Reward columns that have a relevant keyword
                    score = (100 if has_keyword else 10)
                    candidates.append({'col': c, 'data': converted, 'score': score, 'count': valid_count})
            
            if candidates:
                # Winner selection: Highest Keyword Score -> Highest Data Density
                winner = sorted(candidates, key=lambda x: (x['score'], x['count']), reverse=True)[0]
                df[var_name] = winner['data']
                print(f"   🎯 ALPHA Winner for '{sheet}': '{winner['col']}' ({winner['count']} pts)")
            else:
                print(f"   ⚠️ WARNING: No valid labeled macro series found in '{sheet}'.")
                continue

            # --- QUARTERLY DATE PARSING ---
            def parse_period(val):
                try:
                    f_val = float(val)
                    year, rem = int(f_val), f_val - int(f_val)
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
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')