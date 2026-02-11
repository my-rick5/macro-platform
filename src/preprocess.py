import pandas as pd
import os
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #662 Production)... ")
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the Excel workbook
    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"❌ FATAL: Could not load Excel file: {e}")
        return

    # Map Sheet Names to Model Variable Names
    mapping = {
        'unemp': 'adjlegrt', 
        'lur': 'adjlegrt', 
        'gdp': 'anngr', 
        'anngr': 'anngr',
        'pce': 'eco'
    }
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in mapping:
            continue 
            
        var_name = mapping[s_clean]
        try:
            # Skip header row and rename the first column to 'date_raw'
            df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
            df.rename(columns={df.columns[0]: 'date_raw'}, inplace=True)
            
            # --- REFINED HUNTER LOGIC WITH MAGNITUDE GUARD ---
            data_col = None
            for c in df.columns:
                if c == 'date_raw': continue
                
                # Convert to numeric, turning text/garbage into NaN
                converted = pd.to_numeric(df[c], errors='coerce')
                
                # MAGNITUDE GUARD:
                # 1. Must have at least 5 valid numeric points.
                # 2. Maximum absolute value must be < 1000. 
                # (Prevents YYYYMMDD dates like 20100310.0 from being picked as data).
                if converted.notna().sum() > 5 and converted.abs().max() < 1000:
                    df[var_name] = converted
                    data_col = c
                    print(f"   🎯 Valid economic data found in sheet '{sheet}', column: '{c}'")
                    break
            
            if not data_col:
                print(f"   ⚠️ WARNING: No valid economic series found in '{sheet}'. Skipping.")
                continue

            # --- DECIMAL DATE PARSING ---
            # Handles formats like 1967.2 (Q2) or 1967.45 (Q3)
            def parse_period(val):
                try:
                    f_val = float(val)
                    year = int(f_val)
                    rem = f_val - year
                    # Logic to map decimal remainder to Quarter
                    q = 1 if rem < 0.1 else 2 if rem < 0.3 else 3 if rem < 0.6 else 4
                    return f"{year}Q{q}"
                except:
                    return None

            df['date'] = df['date_raw'].apply(parse_period)
            
            # --- DEDUPLICATION & FINAL SAVE ---
            # Drop rows missing either date or the variable
            final_df = df.dropna(subset=['date', var_name])
            
            if not final_df.empty:
                # Collapse multiple observations for the same quarter into the last one
                final_df = final_df.groupby('date')[var_name].last().reset_index()
                
                save_path = os.path.join(output_dir, f"{var_name}.csv")
                final_df.to_csv(save_path, index=False)
                print(f"   ✅ SUCCESS: Saved {len(final_df)} unique quarters to {var_name}.csv")
                
        except Exception as e:
            print(f"   ❌ Error processing sheet '{sheet}': {e}")

if __name__ == "__main__":
    # Standard paths inside the Docker container
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')