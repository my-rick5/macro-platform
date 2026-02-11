import pandas as pd
import os

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #671 Final Strike Hunter)... ")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"❌ FATAL: Could not load Excel file: {e}")
        return

    mapping = {'unemp': 'adjlegrt', 'lur': 'adjlegrt', 'gdp': 'anngr', 'anngr': 'anngr', 'pce': 'eco'}
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in mapping: continue 
            
        var_name = mapping[s_clean]
        try:
            df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
            df.rename(columns={df.columns[0]: 'date_raw'}, inplace=True)
            
            # --- FINAL STRIKE HUNTER ---
            candidates = []
            for c in df.columns:
                if c == 'date_raw': continue
                c_str = str(c).lower()
                converted = pd.to_numeric(df[c], errors='coerce')
                
                # Check how many actual numbers are in the column
                valid_count = converted.notna().sum()
                
                # 1. Density Check: Must have at least 150 points for a full series
                if valid_count > 150: 
                    # 2. Macro Range Check: 
                    # Real unemployment/GDP rates average between -10 and 25.
                    # Dates (20100310) or Versions (3.8.3) will fail this.
                    avg_val = converted.mean()
                    if not (-10 < avg_val < 25): continue
                    
                    # 3. Variance Check: Must be dynamic
                    if converted.std() < 0.01: continue
                    
                    # 4. Keyword Scoring
                    is_date_like = converted.abs().max() > 1000
                    keywords = ['rate', 'unemp', 'lur', 'val', 'adj', var_name]
                    has_keyword = any(k in c_str for k in keywords)
                    
                    score = (15 if has_keyword else 0) - (100 if is_date_like else 0)
                    candidates.append({'col': c, 'data': converted, 'score': score, 'count': valid_count})
            
            if candidates:
                # Prioritize by keyword score, then by the most data points (density)
                winner = sorted(candidates, key=lambda x: (x['score'], x['count']), reverse=True)[0]
                df[var_name] = winner['data']
                print(f"   🎯 FINAL Winner for '{sheet}': '{winner['col']}' ({winner['count']} pts, Mean: {winner['data'].mean():.2f})")
            else:
                print(f"   ⚠️ WARNING: No valid high-density candidates found in '{sheet}'.")
                continue

            # --- DATE PARSING & DEDUPLICATION ---
            def parse_period(val):
                try:
                    f_val = float(val)
                    year, rem = int(f_val), f_val - int(f_val)
                    q = 1 if rem < 0.1 else 2 if rem < 0.3 else 3 if rem < 0.6 else 4
                    return f"{year}Q{q}"
                except: return None

            df['date'] = df['date_raw'].apply(parse_period)
            final_df = df.dropna(subset=['date', var_name])
            if not final_df.empty:
                final_df = final_df.groupby('date')[var_name].last().reset_index()
                final_df.to_csv(os.path.join(output_dir, f"{var_name}.csv"), index=False)
                print(f"   ✅ SUCCESS: Saved {var_name}.csv")
                
        except Exception as e:
            print(f"   ❌ Error processing sheet '{sheet}': {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')