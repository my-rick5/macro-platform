import pandas as pd
import os

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #668 String-Safe Hunter)... ")
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
            
            # --- STRING-SAFE STRICT HUNTER SCORING ---
            candidates = []
            for c in df.columns:
                if c == 'date_raw': continue
                
                # SAFE: Convert header to string before checking keywords
                c_str = str(c).lower()
                
                converted = pd.to_numeric(df[c], errors='coerce')
                valid_count = converted.notna().sum()
                
                if valid_count > 5:
                    # Check range and keywords
                    is_date_like = converted.abs().max() > 1000
                    has_keyword = any(k in c_str for k in ['unemp', 'lur', 'rate', 'val'])
                    
                    # Apply weights: penalty for dates, bonus for keywords
                    score = (10 if has_keyword else 0) - (50 if is_date_like else 0)
                    candidates.append({'col': c, 'data': converted, 'score': score})
            
            if candidates:
                winner = sorted(candidates, key=lambda x: x['score'], reverse=True)[0]
                df[var_name] = winner['data']
                print(f"   🎯 Winner for '{sheet}': '{winner['col']}' (Score: {winner['score']})")
            else:
                print(f"   ⚠️ WARNING: No valid candidates found in '{sheet}'.")
                continue

            # --- DECIMAL DATE PARSING ---
            def parse_period(val):
                try:
                    f_val = float(val)
                    year = int(f_val)
                    rem = f_val - year
                    q = 1 if rem < 0.1 else 2 if rem < 0.3 else 3 if rem < 0.6 else 4
                    return f"{year}Q{q}"
                except: return None

            df['date'] = df['date_raw'].apply(parse_period)
            
            # --- DEDUPLICATION ---
            final_df = df.dropna(subset=['date', var_name])
            if not final_df.empty:
                final_df = final_df.groupby('date')[var_name].last().reset_index()
                final_df.to_csv(os.path.join(output_dir, f"{var_name}.csv"), index=False)
                print(f"   ✅ SUCCESS: Saved {var_name}.csv")
                
        except Exception as e:
            print(f"   ❌ Error processing sheet '{sheet}': {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')