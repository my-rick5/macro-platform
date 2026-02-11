import pandas as pd
import os

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Magnitude Guard Fix)... ")
    os.makedirs(output_dir, exist_ok=True)
    
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
            df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
            df.rename(columns={df.columns[0]: 'date_raw'}, inplace=True)
            
            # --- HUNTER LOGIC WITH MAGNITUDE GUARD ---
            data_col = None
            for c in df.columns:
                if c == 'date_raw': continue
                
                converted = pd.to_numeric(df[c], errors='coerce')
                
                # MAGNITUDE GUARD:
                # Skips any column where the max value is > 1000.
                # This ignores YYYYMMDD dates (like 20100310.0) and finds real rates.
                if converted.notna().sum() > 5 and converted.abs().max() < 1000:
                    df[var_name] = converted
                    data_col = c
                    print(f"   🎯 Valid economic data found in '{sheet}' -> column: '{c}'")
                    break
            
            if not data_col:
                print(f"   ⚠️ WARNING: No valid economic series found in '{sheet}'. Skipping.")
                continue

            # --- DECIMAL DATE PARSING ---
            def parse_period(val):
                try:
                    f_val = float(val)
                    year = int(f_val)
                    rem = f_val - year
                    q = 1 if rem < 0.1 else 2 if rem < 0.3 else 3 if rem < 0.6 else 4
                    return f"{year}Q{q}"
                except:
                    return None

            df['date'] = df['date_raw'].apply(parse_period)
            
            # --- DEDUPLICATION ---
            final_df = df.dropna(subset=['date', var_name])
            if not final_df.empty:
                final_df = final_df.groupby('date')[var_name].last().reset_index()
                final_df.to_csv(os.path.join(output_dir, f"{var_name}.csv"), index=False)
                print(f"   ✅ SUCCESS: Saved {var_name}.csv")
                
        except Exception as e:
            print(f"   ❌ Error processing sheet '{sheet}': {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')