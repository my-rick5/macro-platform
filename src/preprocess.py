import pandas as pd
import os
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #649 Verified Save)... ")
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(excel_path):
        print(f"❌ FATAL: Excel library not found at {excel_path}")
        return

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
            
            # 1. Dynamic Scraper (Verified in Build #648)
            data_col = None
            for col in df.columns:
                if col == 'date_raw': continue
                converted = pd.to_numeric(df[col], errors='coerce')
                
                # Check for economic data (values < 1000) with sufficient observation count
                if converted.notna().sum() > 5 and converted.abs().max() < 1000:
                    df[var_name] = converted
                    data_col = col
                    print(f"   🎯 Data found in column: '{col}'")
                    break
            
            if not data_col:
                print(f"   ❌ No numeric data column found in '{sheet}'")
                continue

            # 2. Date Parsing
            def parse_period(val):
                s = str(val).strip()
                match = re.search(r'(\d{4})Q(\d)', s)
                return f"{match.group(1)}Q{match.group(2)}" if match else None

            df['date'] = df['date_raw'].apply(parse_period)
            final_df = df.dropna(subset=['date', var_name])
            
            # 3. Verified Save Logic
            print(f"   📊 Rows to save: {len(final_df)}")
            if len(final_df) > 0:
                save_path = os.path.join(output_dir, f"{var_name}.csv")
                
                # Use a standard save without PeriodIndex to avoid serialization issues
                final_df[['date', var_name]].to_csv(save_path, index=False)
                
                if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                    print(f"   ✅ VERIFIED: {save_path} saved ({os.path.getsize(save_path)} bytes).")
                else:
                    print(f"   ❌ CRITICAL: File system failed to write {save_path}")
            else:
                sample_dates = df['date_raw'].head(2).tolist()
                print(f"   ⚠️ ERROR: Date parsing resulted in 0 rows. Check format: {sample_dates}")
            
        except Exception as e:
            print(f"   ❌ FAILED processing sheet {sheet}: {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')