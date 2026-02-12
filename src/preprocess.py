import pandas as pd
import os
import shutil

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #707 Force-Wipe)... ")
    
    # --- THE OS-LEVEL PURGE ---
    # We use os.system to bypass Python file-handle locks that might prevent 
    # shutil from clearing bind-mounted Docker volumes.
    try:
        if os.path.exists(output_dir):
            os.system(f"rm -rf {output_dir}/*")
            print(f"   💥 OS-LEVEL WIPE: Contents of {output_dir} deleted.")
        else:
            os.makedirs(output_dir, exist_ok=True)
            print(f"   📁 CREATED: New output directory at {output_dir}")
    except Exception as e:
        print(f"   ⚠️ WIPE WARNING: {e}")

    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"❌ FATAL: Could not load Excel file: {e}")
        return

    # THE WHITE LIST: Explicitly allow only these headers
    allowed_headers = ['DATE', 'UNEMPF0', 'REALGDPF0', 'PCEF0', 'LURF0']
    
    # Map sheets to engine-specific unique filenames
    mapping = {
        'unemp': 'labor_series', 
        'lur':   'labor_series', 
        'gdp':   'gdp_series', 
        'pce':   'pce_anchor'
    }
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in mapping: continue 
            
        var_name = mapping[s_clean]
        try:
            df = pd.read_excel(xls, sheet_name=sheet)
            
            # --- AUDIT & PURGE ---
            print(f"   🔍 SHEET: {sheet}")
            
            # Filter columns against the White List (stripping whitespace and casing)
            cols_to_keep = [c for c in df.columns if str(c).upper().strip() in allowed_headers]
            df = df[cols_to_keep]
            print(f"      🛡️  REMAINING AFTER PURGE: {list(df.columns)}")

            # Find target Nowcast (F0)
            target = None
            for col in df.columns:
                if 'F0' in str(col).upper():
                    target = col
                    break

            if not target:
                print(f"      ⚠️  No valid F0 target found. Skipping sheet.")
                continue

            # --- DEDUPLICATION ---
            temp_df = pd.DataFrame({
                'raw_date': df.iloc[:, 0],
                'value': pd.to_numeric(df[target], errors='coerce')
            }).dropna()

            def parse_period(val):
                try:
                    f_val = float(val)
                    year, rem = int(f_val), f_val - int(f_val)
                    q = 1 if rem < 0.15 else 2 if rem < 0.4 else 3 if rem < 0.65 else 4
                    return f"{year}Q{q}"
                except: return None

            temp_df['date'] = temp_df['raw_date'].apply(parse_period)
            
            # Take the LAST vintage entry for each quarter
            final_df = temp_df.dropna(subset=['date']).groupby('date').last().reset_index()
            final_df = final_df[['date', 'value']].rename(columns={'value': var_name})

            # Save clean file for Engine consumption
            final_df.to_csv(os.path.join(output_dir, f"{var_name}.csv"), index=False)
            print(f"      ✅ SUCCESS: Saved {var_name}.csv")
                
        except Exception as e:
            print(f"      ❌ ERROR processing sheet '{sheet}': {e}")

if __name__ == "__main__":
    # Internal container paths for the Jenkins/Docker environment
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')