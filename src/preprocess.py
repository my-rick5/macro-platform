import pandas as pd
import os
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #646 Merged)... ")
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(excel_path):
        print(f"❌ FATAL: Excel library not found at {excel_path}"); return

    xls = pd.ExcelFile(excel_path)
    
    # Flexible mapping to catch varied sheet naming conventions
    mapping = {
        'anngr': 'anngr', 'gdp': 'anngr',
        'delrff': 'delrff', 'ffr': 'delrff',
        'lur': 'adjlegrt', 'unemp': 'adjlegrt',
        'grm': 'ddockm', 'imports': 'ddockm',
        'grx': 'ddockx', 'exports': 'ddockx'
    }
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in mapping:
            continue 
            
        var_name = mapping[s_clean]
        print(f"🔎 Processing Target: '{sheet}' -> '{var_name}'")
        
        try:
            df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
            
            # 1. Identify Date (1st col) and Data (2nd col)
            df.rename(columns={df.columns[0]: 'date_raw'}, inplace=True)
            target_col = df.columns[1] 
            df[var_name] = pd.to_numeric(df[target_col], errors='coerce')
            
            # 2. Robust Date Parsing
            def parse_period(val):
                s = str(val).strip()
                match = re.search(r'(\d{4})Q(\d)', s)
                return f"{match.group(1)}Q{match.group(2)}" if match else None

            df['date'] = df['date_raw'].apply(parse_period)
            
            # 3. Clean & Validate
            final_df = df.dropna(subset=['date', var_name])
            if final_df.empty:
                print(f"   ⚠️ WARNING: Sheet '{sheet}' resulted in 0 valid data rows. Skipping.")
                continue

            final_df = final_df[['date', var_name]].drop_duplicates(subset=['date'], keep='last')
            
            # 4. Save
            save_path = os.path.join(output_dir, f"{var_name}.csv")
            final_df.set_index('date').sort_index().to_csv(save_path)
            print(f"   ✅ SUCCESS: Saved {len(final_df)} rows to {save_path}")
            
        except Exception as e:
            print(f"   ❌ FAILED sheet {sheet}: {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')