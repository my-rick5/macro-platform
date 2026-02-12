import pandas as pd
import os
import shutil

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #717 Sync & Destroy)... ")
    
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

    # Whitelist of approved headers
    allowed_headers = ['DATE', 'UNEMPF0', 'REALGDPF0', 'PCEF0', 'LURF0']
    
    # SYNCED MAPPING: Filenames now match the residual headers exactly
    mapping = {
        'unemp': 'unemp',  # Overwrites the corrupted unemp.csv
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
            df = df[cols_to_keep]

            # Identify target Nowcast
            target = None
            for col in df.columns:
                if 'F0' in str(col).upper():
                    target = col
                    break

            if not target: continue

            # --- VALUE GUARD ---
            temp_df = pd.DataFrame({
                'raw_date': df.iloc[:, 0],
                'value': pd.to_numeric(df[target], errors='coerce')
            })

            # Explicitly strip out YYYYMMDD date stamps (> 1000)
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

            # Save clean file with the exact name the engine expects
            out_file = os.path.join(output_dir, f"{var_name}.csv")
            final_df.to_csv(out_file, index=False)
            
            # --- AUDIT PREVIEW ---
            print(f"      🎯 TARGET SYNC: Saved {var_name}.csv to {out_file}")
            print(f"      📊 DATA PREVIEW:")
            print(final_df.head(5).to_string(index=False))
            print("-" * 30)
                
        except Exception as e:
            print(f"      ❌ ERROR in sheet '{sheet}': {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')