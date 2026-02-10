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
        # Load raw data to inspect
        df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
        if df.empty: continue

        # 1. First column is our Date
        df.rename(columns={df.columns[0]: 'date_raw'}, inplace=True)
        
        # 2. Map Variable Name
        var_name = 'LUR' if 'unemp' in sheet.lower() else sheet.upper()
        
        # 3. Standardize Dates
        def parse_period(val):
            s = str(val).strip()
            s = re.sub(r'[:.\- ]', 'Q', s)
            match = re.search(r'(\d{4})Q(\d)', s)
            return f"{match.group(1)}Q{match.group(2)}" if match else None

        df['date'] = df['date_raw'].apply(parse_period)
        
        # 4. DATA EXTRACTION: Force numeric conversion on all but the date
        # We look for the last column that contains mostly numbers
        data_col = None
        for col in reversed(df.columns[1:-1]): # Search backwards, skip the date and the very last potential empty col
            converted = pd.to_numeric(df[col], errors='coerce')
            # If at least 50% of the column is numeric and values are reasonable
            if converted.notna().sum() > (len(df) * 0.5):
                # Filter out those huge date-integers (e.g. 19670426)
                if converted.abs().max() < 1000:
                    df[var_name] = converted
                    data_col = col
                    break
        
        if data_col:
            final_df = df.dropna(subset=['date', var_name])
            if not final_df.empty:
                try:
                    final_df = final_df[['date', var_name]].copy()
                    final_df['date'] = pd.PeriodIndex(final_df['date'], freq='Q')
                    save_path = os.path.join(output_dir, f"{var_name.lower()}.csv")
                    final_df.set_index('date').sort_index().to_csv(save_path)
                    print(f"   ✅ Saved {var_name} ({len(final_df)} obs). Latest: {final_df[var_name].iloc[-1]}")
                except Exception as e:
                    print(f"   ❌ Formatting error: {e}")
            else:
                print(f"   ⚠️ No valid rows after cleaning.")
        else:
            print(f"   ❌ Could not find a valid numeric data column.")

    print(f"🏁 Finished. Created {len(os.listdir(output_dir))} valid data files.")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')