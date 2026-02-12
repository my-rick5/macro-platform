import pandas as pd
import os
import shutil

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #710 Host-Check)... ")
    
    # --- PARENT AUDIT ---
    # We check the parent to see if ghost files (import.csv, etc.) are hiding one level up
    parent_dir = os.path.dirname(output_dir)
    try:
        if os.path.exists(parent_dir):
            print(f"   📂 Parent Directory Audit ({parent_dir}):")
            print(f"      Contents: {os.listdir(parent_dir)}")
    except Exception as e:
        print(f"   ⚠️ Parent Audit Failed: {e}")

    # --- AGGRESSIVE WIPE ---
    # Using shell to force-delete the directory and recreate it fresh
    try:
        os.system(f"rm -rf {output_dir} && mkdir -p {output_dir}")
        remaining = os.listdir(output_dir) if os.path.exists(output_dir) else []
        print(f"   💥 CLEANED & RECREATED: {output_dir}")
        print(f"   🧹 Post-Wipe Check: {len(remaining)} files remain in target.")
    except Exception as e:
        print(f"   ⚠️ Force-Wipe Failed: {e}")

    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"❌ FATAL: Could not load Excel file: {e}")
        return

    # Whitelist of approved headers
    allowed_headers = ['DATE', 'UNEMPF0', 'REALGDPF0', 'PCEF0', 'LURF0']
    
    # Mapping to engine-specific filenames
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
            
            # --- PURGE NON-WHITELISTED ---
            # This kills GBdate, UNEMPB1, etc.
            cols_to_keep = [c for c in df.columns if str(c).upper().strip() in allowed_headers]
            df = df[cols_to_keep]

            # Identify target Nowcast
            target = None
            for col in df.columns:
                if 'F0' in str(col).upper():
                    target = col
                    break

            if not target:
                continue

            # --- STANDARDIZE & DEDUPLICATE ---
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
            
            # Group by the Quarter and take the last row (latest vintage)
            final_df = temp_df.dropna(subset=['date']).groupby('date').last().reset_index()
            final_df = final_df[['date', 'value']].rename(columns={'value': var_name})

            # Save clean file
            out_path = os.path.join(output_dir, f"{var_name}.csv")
            final_df.to_csv(out_path, index=False)
            print(f"      ✅ SUCCESS: Saved {var_name}.csv to {out_path}")
                
        except Exception as e:
            print(f"      ❌ ERROR in sheet '{sheet}': {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')