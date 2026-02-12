import pandas as pd
import os

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #720 - Stricter Targeting)... ")
    
    # --- ABSOLUTE WIPE ---
    try:
        if os.path.exists(output_dir):
            os.system(f"rm -rf {output_dir}/*")
            print(f"   💥 OS-LEVEL WIPE: {output_dir} cleared.")
        else:
            os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        print(f"   ⚠️ Wipe failed: {e}")

    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"❌ FATAL: Could not load Excel file: {e}")
        return

    # Whitelist of approved headers for the initial load
    allowed_headers = ['DATE', 'UNEMPF0', 'REALGDPF0', 'PCEF0', 'LURF0']
    
    # SYNCED MAPPING: Using 'unemp' to match the Residual Header exactly
    mapping = {
        'unemp': 'unemp', 
        'lur':   'unemp', 
        'gdp':   'gdp', 
        'pce':   'pce'
    }
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in mapping: continue 
            
        var_name = mapping[s_clean]
        try:
            df = pd.read_excel(xls, sheet_name=sheet)
            
            # --- PURGE NON-WHITELISTED ---
            cols_to_keep = [c for c in df.columns if str(c).upper().strip() in allowed_headers]
            # If no whitelist hits, keep all columns to avoid empty DF, but we will filter next
            if cols_to_keep:
                df = df[cols_to_keep]

            # --- STRICTER TARGET SELECTION ---
            # We need the column with 'F0' that is NOT a Date or ID
            target = None
            for col in df.columns:
                c_upper = str(col).upper().strip()
                if 'F0' in c_upper and all(x not in c_upper for x in ['DATE', 'PERIOD', 'STAMP']):
                    target = col
                    break

            if not target:
                print(f"      ⚠️ WARNING: Could not find valid F0 value column in '{sheet}'. Skipping.")
                continue

            print(f"      🎯 TARGET FOUND: In sheet '{sheet}', selected column '{target}'")

            # --- VALUE GUARD ---
            temp_df = pd.DataFrame({
                'raw_date': df.iloc[:, 0],
                'value': pd.to_numeric(df[target], errors='coerce')
            })

            # Logic: If 'value' looks like a date (e.g. 20100310), it's > 1000. 
            # We filter those out. If the whole column is dates, the result is empty.
            temp_df = temp_df[temp_df['value'] < 1000].dropna()

            if temp_df.empty:
                print(f"      ❌ REJECTED: Column '{target}' contained only dates/invalid values.")
                continue

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

            # --- THE TOTAL TAKEOVER ---
            possible_dirs = [
                output_dir,                     # /home/spark/data/processed
                "/home/spark/data",             
                "/home/spark/external_data",    
                "/home/spark"                   
            ]
            
            for d in possible_dirs:
                if os.path.exists(d):
                    target_path = os.path.join(d, f"{var_name}.csv")
                    final_df.to_csv(target_path, index=False)
                    print(f"      🚀 OVERWROTE: {target_path}")
            
            # --- AUDIT PREVIEW ---
            print(f"      📊 DATA PREVIEW FOR {var_name}:")
            print(final_df.head(3).to_string(index=False))
            print("-" * 30)
                
        except Exception as e:
            print(f"      ❌ ERROR in sheet '{sheet}': {e}")

if __name__ == "__main__":
    # In Jenkins/Docker, we check local directory 'processed'
    clean_fed_excel('library.xlsx', './processed')