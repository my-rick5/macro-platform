import pandas as pd
import os
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #639 Protection)... ")
    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    
    # HARD-CODED MAPPING: Ensure these exact sheet names map to model variables
# More flexible mapping to catch variations in your Excel sheets
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
            continue # Skip unknown sheets to prevent "Date Integrity" errors
            
        var_name = mapping[s_clean]
        print(f"🔎 Processing Core Target: '{sheet}' -> '{var_name}'")
        
        df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
        
        # 1. IDENTIFY DATE: Usually the first column
        df.rename(columns={df.columns[0]: 'date_raw'}, inplace=True)
        
        # 2. IDENTIFY DATA: Use the SECOND column (skipping the date-serial column)
        # This prevents the 2.01e+07 error seen in Build #638
        try:
            target_col = df.columns[1] 
            df[var_name] = pd.to_numeric(df[target_col], errors='coerce')
            
            def parse_period(val):
                s = str(val).strip()
                match = re.search(r'(\d{4})Q(\d)', s)
                return f"{match.group(1)}Q{match.group(2)}" if match else None

            df['date'] = df['date_raw'].apply(parse_period)
            
            # 3. SAVE
            final_df = df.dropna(subset=['date', var_name])
            final_df = final_df[['date', var_name]].drop_duplicates(subset=['date'], keep='last')
            
            save_path = os.path.join(output_dir, f"{var_name}.csv")
            final_df.set_index('date').to_csv(save_path)
            print(f"   ✅ SUCCESS: Saved {save_path}")
            
        except Exception as e:
            print(f"   ❌ FAILED sheet {sheet}: {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')