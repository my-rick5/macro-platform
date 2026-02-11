import pandas as pd
import os
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #656 Deduplication)... ")
    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    
    mapping = {'unemp': 'adjlegrt', 'lur': 'adjlegrt', 'gdp': 'anngr', 'anngr': 'anngr'}
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in mapping: continue 
            
        var_name = mapping[s_clean]
        try:
            df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
            df.rename(columns={df.columns[0]: 'date_raw'}, inplace=True)
            
            # 1. Scraper for numeric data
            data_col = next((c for c in df.columns if c != 'date_raw' and 
                             pd.to_numeric(df[c], errors='coerce').notna().sum() > 5), None)
            if not data_col: continue
            df[var_name] = pd.to_numeric(df[data_col], errors='coerce')

            # 2. Decimal Date Parsing (Fixed for 1967.2 format)
            def parse_period(val):
                try:
                    f_val = float(val)
                    year = int(f_val)
                    rem = f_val - year
                    q = 1 if rem < 0.1 else 2 if rem < 0.3 else 3 if rem < 0.6 else 4
                    return f"{year}Q{q}"
                except: return None

            df['date'] = df['date_raw'].apply(parse_period)
            
            # 3. 🧹 Deduplication: Collapse multiple monthly/duplicate rows into one quarter
            final_df = df.dropna(subset=['date', var_name])
            if not final_df.empty:
                print(f"   🧹 Collapsing duplicates for {var_name}...")
                # Use the last observation for each quarter
                final_df = final_df.groupby('date')[var_name].last().reset_index()
                
                save_path = os.path.join(output_dir, f"{var_name}.csv")
                final_df.to_csv(save_path, index=False)
                print(f"   ✅ VERIFIED: Saved {len(final_df)} unique quarters.")
                
        except Exception as e:
            print(f"   ❌ FAILED sheet {sheet}: {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')