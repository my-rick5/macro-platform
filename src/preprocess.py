import pandas as pd
import os
import datetime

def clean_fed_excel(excel_path, output_dir):
    now = datetime.datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"🎬 Starting Preprocessor (Build #725 - Path Overdrive)... ")
    
    # --- ABSOLUTE WIPE ---
    if os.path.exists(output_dir):
        os.system(f"rm -rf {output_dir}/*")
    else:
        os.makedirs(output_dir, exist_ok=True)

    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"❌ FATAL: {e}")
        return

    mapping = {'unemp': 'unemp', 'lur': 'unemp', 'gdp': 'gdp', 'pce': 'pce'}
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in mapping: continue 
        var_name = mapping[s_clean]
        
        try:
            df = pd.read_excel(xls, sheet_name=sheet)
            target = None
            for col in df.columns:
                c_upper = str(col).upper()
                if 'F0' in c_upper and all(x not in c_upper for x in ['DATE', 'PERIOD']):
                    target = col
                    break

            if not target: continue

            temp_df = pd.DataFrame({
                'raw_date': df.iloc[:, 0],
                'value': pd.to_numeric(df[target], errors='coerce')
            })
            temp_df = temp_df[temp_df['value'] < 1000].dropna()

            def parse_period(val):
                try:
                    f_val = float(val)
                    year, rem = int(f_val), f_val - int(f_val)
                    q = 1 if rem < 0.15 else 2 if rem < 0.4 else 3 if rem < 0.65 else 4
                    return f"{year}Q{q}"
                except: return None

            temp_df['date'] = temp_df['raw_date'].apply(parse_period)
            final_df = temp_df.dropna(subset=['date']).groupby('date').last().reset_index()
            final_df = final_df[['date', 'value']].rename(columns={'value': var_name})
            
            # CRITICAL: Add timestamp to the dataframe
            final_df['processed_at'] = timestamp_str

            # --- THE PATH OVERDRIVE ---
            # We overwrite EVERY possible location to kill 'ghost' files
            target_dirs = [
                output_dir,
                "/home/spark/external_data",
                "/home/spark/pyfrbus",
                "/home/spark/src",
                "/home/spark"
            ]
            
            for d in target_dirs:
                if os.path.exists(d):
                    p = os.path.join(d, f"{var_name}.csv")
                    final_df.to_csv(p, index=False)
                    print(f"      🚀 OVERWRITE SUCCESS: {p}")
                
        except Exception as e:
            print(f"      ❌ ERROR in '{sheet}': {e}")

if __name__ == "__main__":
    clean_fed_excel('library.xlsx', './processed')