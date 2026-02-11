import pandas as pd
import os
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor Trace...")
    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    
    # Updated mapping with case-insensitive logic
    mapping = {
        'anngr': 'anngr',
        'delrff': 'delrff',
        'lur': 'adjlegrt',
        'grm': 'ddockm',
        'grx': 'ddockx'
    }
    
    print(f"📋 Sheets found in Excel: {xls.sheet_names}")
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean in ['documentation', 'notes', 'summary', 'definitions']:
            continue
            
        var_name = mapping.get(s_clean, s_clean)
        # Force 'unemp' keyword to labor variable
        if 'unemp' in s_clean: var_name = 'adjlegrt'
        
        print(f"🔎 Checking Sheet: '{sheet}' -> Target: '{var_name}'")
        
        try:
            df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
            if df.empty:
                print(f"   ⚠️ Sheet '{sheet}' is empty.")
                continue

            # Standardize Date Column
            df.rename(columns={df.columns[0]: 'date_raw'}, inplace=True)
            
            def parse_period(val):
                s = str(val).strip()
                s = re.sub(r'[:.\- ]', 'Q', s)
                match = re.search(r'(\d{4})Q(\d)', s)
                return f"{match.group(1)}Q{match.group(2)}" if match else None

            df['date'] = df['date_raw'].apply(parse_period)
            
            # Data Search
            data_col = None
            for col in reversed(df.columns):
                if col in ['date', 'date_raw']: continue
                
                converted = pd.to_numeric(df[col], errors='coerce')
                valid_count = converted.notna().sum()
                
                if valid_count > 5: # Lowered threshold to catch smaller trade sets
                    df[var_name] = converted
                    data_col = col
                    break
            
            if data_col:
                final_df = df.dropna(subset=['date', var_name])
                final_df = final_df[['date', var_name]].copy()
                final_df = final_df.drop_duplicates(subset=['date'], keep='last')
                
                final_df['date'] = pd.PeriodIndex(final_df['date'], freq='Q')
                save_name = f"{var_name.lower()}.csv"
                save_path = os.path.join(output_dir, save_name)
                
                final_df.set_index('date').sort_index().to_csv(save_path)
                print(f"   ✅ SUCCESS: Saved as {save_name} ({len(final_df)} obs)")
            else:
                print(f"   ❌ FAILURE: No numeric data found in '{sheet}'")

        except Exception as e:
            print(f"   ❌ ERROR processing '{sheet}': {e}")

    print(f"🏁 Final Processed Files: {os.listdir(output_dir)}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')