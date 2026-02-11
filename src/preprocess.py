import pandas as pd
import os
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #648 Scraper Mode)... ")
    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    
    mapping = {
        'anngr': 'anngr', 'gdp': 'anngr',
        'delrff': 'delrff', 'ffr': 'delrff',
        'lur': 'adjlegrt', 'unemp': 'adjlegrt',
        'grm': 'ddockm', 'grx': 'ddockx'
    }
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in mapping:
            continue 
            
        var_name = mapping[s_clean]
        print(f"🔎 Scanning Sheet: '{sheet}' for numeric data...")
        
        try:
            df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
            df.rename(columns={df.columns[0]: 'date_raw'}, inplace=True)
            
            # --- NEW DYNAMIC SCRAPER ---
            data_col = None
            for col in df.columns:
                if col == 'date_raw': continue
                
                # Try to convert this column to numbers
                converted = pd.to_numeric(df[col], errors='coerce')
                
                # Look for columns with meaningful data density
                # Values < 1000 avoids date-integers; > 5 obs ensures it's not a dummy col
                if converted.notna().sum() > 5 and converted.abs().max() < 1000:
                    df[var_name] = converted
                    data_col = col
                    print(f"   🎯 Data found in: '{col}'")
                    break
            
            if not data_col:
                print(f"   ❌ No numeric data column found in '{sheet}'")
                continue

            def parse_period(val):
                s = str(val).strip()
                match = re.search(r'(\d{4})Q(\d)', s)
                return f"{match.group(1)}Q{match.group(2)}" if match else None

            df['date'] = df['date_raw'].apply(parse_period)
            final_df = df.dropna(subset=['date', var_name])
            
            if not final_df.empty:
                save_path = os.path.join(output_dir, f"{var_name}.csv")
                final_df[['date', var_name]].set_index('date').to_csv(save_path)
                print(f"   ✅ SUCCESS: Saved {len(final_df)} rows.")
            
        except Exception as e:
            print(f"   ❌ FAILED sheet {sheet}: {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')