import pandas as pd
import os
import re
import numpy as np

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Mapping Enabled)...")
    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    
    # Define FRB/US Variable Mapping
    # Sheet Name -> Model Variable Name
    mapping = {
        'anngr': 'anngr',      # GDP
        'delrff': 'delrff',    # Fed Funds
        'lur': 'adjlegrt',     # Labor (Standardized name)
        'grm': 'ddockm',       # Real Imports
        'grx': 'ddockx'        # Real Exports
    }
    
    for sheet in xls.sheet_names:
        s_lower = sheet.lower()
        if s_lower in ['documentation', 'notes', 'summary', 'definitions']:
            continue
            
        print(f"🔎 Processing Sheet: {sheet}")
        df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
        if df.empty: continue

        # 1. Determine Target Filename
        # If the sheet is in our map, use the map. Otherwise, use sheet name.
        var_name = mapping.get(s_lower, s_lower)
        if 'unemp' in s_lower: var_name = 'adjlegrt'

        # 2. First column is our Date
        df.rename(columns={df.columns[0]: 'date_raw'}, inplace=True)
        
        # 3. Standardize Dates
        def parse_period(val):
            s = str(val).strip()
            s = re.sub(r'[:.\- ]', 'Q', s)
            match = re.search(r'(\d{4})Q(\d)', s)
            return f"{match.group(1)}Q{match.group(2)}" if match else None

        df['date'] = df['date_raw'].apply(parse_period)
        
        # 4. DATA EXTRACTION
        data_col = None
        for col in reversed(df.columns):
            if col in ['date', 'date_raw']: continue
            
            converted = pd.to_numeric(df[col], errors='coerce')
            valid_count = converted.notna().sum()
            
            if valid_count > 10:
                # Max value check: excludes date-style integers (e.g. 20240101)
                if converted.abs().max() < 10000:
                    df[var_name] = converted
                    data_col = col
                    break
        
        if data_col:
            # 5. DEDUPLICATION
            final_df = df.dropna(subset=['date', var_name])
            final_df = final_df[['date', var_name]].copy()
            final_df = final_df.drop_duplicates(subset=['date'], keep='last')
            
            try:
                # Ensure date is a PeriodIndex for proper sorting
                final_df['date'] = pd.PeriodIndex(final_df['date'], freq='Q')
                save_path = os.path.join(output_dir, f"{var_name.lower()}.csv")
                final_df.set_index('date').sort_index().to_csv(save_path)
                print(f"   ✅ Saved {var_name} ({len(final_df)} obs).")
            except Exception as e:
                print(f"   ❌ Formatting error: {e}")
        else:
            print(f"   ❌ No valid data found in sheet '{sheet}'.")

    print(f"🏁 Finished. Files in {output_dir}: {os.listdir(output_dir)}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')