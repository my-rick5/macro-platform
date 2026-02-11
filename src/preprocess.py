import pandas as pd
import os

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #670 Validation Hunter)... ")
    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    
    mapping = {'unemp': 'adjlegrt', 'lur': 'adjlegrt', 'gdp': 'anngr', 'anngr': 'anngr', 'pce': 'eco'}
    
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
                c_str = str(c).lower()
                converted = pd.to_numeric(df[c], errors='coerce')
                valid_count = converted.notna().sum()
                
                # REFINEMENT 1: High Density (100+ points)
                if valid_count > 100:
                    # REFINEMENT 2: Variance Check (Must be dynamic data, not a constant 1.0)
                    std_dev = converted.std()
                    if std_dev < 0.001: continue
                    
                    # REFINEMENT 3: Magnitude Guard (No dates)
                    is_date_like = converted.abs().max() > 1000
                    
                    # REFINEMENT 4: Keyword Scoring
                    keywords = ['rate', 'lur', 'unemp', 'index', 'pce', 'adj', var_name]
                    has_keyword = any(k in c_str for k in keywords)
                    exact_match = (c_str == var_name or c_str == s_clean)
                    
                    score = (20 if exact_match else 0) + (10 if has_keyword else 0) - (100 if is_date_like else 0)
                    candidates.append({'col': c, 'data': converted, 'score': score, 'count': valid_count})
            
            if candidates:
                winner = sorted(candidates, key=lambda x: (x['score'], x['count']), reverse=True)[0]
                df[var_name] = winner['data']
                print(f"   🎯 Winner for '{sheet}': '{winner['col']}' (Score: {winner['score']}, StdDev: {winner['data'].std():.4f})")
            else:
                continue

            # Date Parsing & Save
            def parse_period(val):
                try:
                    f_val = float(val)
                    year, rem = int(f_val), f_val - int(f_val)
                    q = 1 if rem < 0.1 else 2 if rem < 0.3 else 3 if rem < 0.6 else 4
                    return f"{year}Q{q}"
                except: return None

            df['date'] = df['date_raw'].apply(parse_period)
            final_df = df.dropna(subset=['date', var_name]).groupby('date')[var_name].last().reset_index()
            final_df.to_csv(os.path.join(output_dir, f"{var_name}.csv"), index=False)
            print(f"   ✅ SUCCESS: Saved {var_name}.csv")
                
        except Exception as e:
            print(f"   ❌ Error in {sheet}: {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')