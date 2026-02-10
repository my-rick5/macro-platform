import pandas as pd
import os
import re
import numpy as np

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor...")
    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    
    for sheet in xls.sheet_names:
        if sheet.lower() in ['documentation', 'notes', 'summary', 'definitions']:
            continue
            
        print(f"🔎 Processing Sheet: {sheet}")
        df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
        if df.empty: continue

        # 1. First column is our Date
        df.rename(columns={df.columns[0]: 'date_raw'}, inplace=True)
        var_name = 'LUR' if 'unemp' in sheet.lower() else sheet.upper()
        
        # 2. Standardize Dates
        def parse_period(val):
            s = str(val).strip()
            s = re.sub(r'[:.\- ]', 'Q', s)
            match = re.search(r'(\d{4})Q(\d)', s)
            return f"{match.group(1)}Q{match.group(2)}" if match else None

        df['date'] = df['date_raw'].apply(parse_period)
        
        # 3. BETTER DATA EXTRACTION: Try all columns from right to left
        data_col = None
        for col in reversed(df.columns):
            if col in ['date', 'date_raw']: continue
            
            converted = pd.to_numeric(df[col], errors='coerce')
            valid_count = converted.notna().sum()
            
            # If we find at least some valid numbers that aren't date-integers
            if valid_count > 10:
                # Sanity check: is it a date like 19670426?
                if converted.abs().max() < 2000:
                    df[var_name] = converted
                    data_col = col
                    break
        
        if data_col:
            # 4. DEDUPLICATION: Ensure one value per quarter
            final_df = df.dropna(subset=['date', var_name])
            final_df = final_df[['date', var_name]].copy()
            
            # Keep only the LAST entry for any duplicate quarter
            final_df = final_df.drop_duplicates(subset=['date'], keep='last')
            
            try:
                final_df['date'] = pd.PeriodIndex(final_df['date'], freq='Q')
                save_path = os.path.join(output_dir, f"{var_name.lower()}.csv")
                final_df.set_index('date').sort_index().to_csv(save_path)
                print(f"   ✅ Saved {var_name} ({len(final_df)} obs). Latest: {final_df[var_name].iloc[-1]}")
            except Exception as e:
                print(f"   ❌ Formatting error: {e}")
        else:
            print(f"   ❌ Could not find valid data column in sheet '{sheet}'.")

    print(f"🏁 Finished. Created {len(os.listdir(output_dir))} valid data files.")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')