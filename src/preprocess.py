import pandas as pd
import os

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #675 Tiered Hunter)... ")
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
            
            # --- TIERED HUNTER LOGIC ---
            gold_candidates = []
            silver_candidates = []
            
            for c in df.columns:
                if c == 'date_raw': continue
                c_str = str(c).lower()
                if c_str.count('.') >= 2: continue # Version Guard
                
                converted = pd.to_numeric(df[c], errors='coerce')
                valid_count = converted.notna().sum()
                
                # Broaden search: require at least 100 points
                if valid_count > 100: 
                    avg_val = converted.mean()
                    if not (-10 < avg_val < 25): continue
                    
                    keywords = ['rate', 'unemp', 'lur', 'val', 'adj', 'index', var_name]
                    has_keyword = any(k in c_str for k in keywords)
                    
                    candidate = {'col': c, 'data': converted, 'count': valid_count}
                    if has_keyword:
                        gold_candidates.append(candidate)
                    else:
                        silver_candidates.append(candidate)
            
            # Selection Priority: Gold (Keywords) -> Silver (Density)
            final_selection = sorted(gold_candidates, key=lambda x: x['count'], reverse=True) or \
                              sorted(silver_candidates, key=lambda x: x['count'], reverse=True)

            if final_selection:
                winner = final_selection[0]
                df[var_name] = winner['data']
                print(f"   🎯 TIERED Winner for '{sheet}': '{winner['col']}' ({winner['count']} pts)")
            else:
                print(f"   ⚠️ WARNING: No valid economic series found in '{sheet}'.")
                continue

            # Date Parsing & Final Deduplication
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
            print(f"   ❌ Error processing sheet '{sheet}': {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')