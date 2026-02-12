import pandas as pd
import os
import shutil

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #705 Audit Mode)... ")
    
    # 1. ABSOLUTE WIPE: Kills any ghost 'import/export' files from the volume
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        print(f"   🧹 DIRECTORY WIPED: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"❌ FATAL: Could not load Excel file: {e}")
        return

    # THE WHITE LIST: If it's not here, it's purged.
    allowed_headers = ['DATE', 'UNEMPF0', 'REALGDPF0', 'PCEF0', 'LURF0']
    
    # Map sheets to unique engine filenames
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
            
            # --- AUDIT LOGGING ---
            raw_cols = [str(c) for c in df.columns]
            print(f"   🔍 SHEET: {sheet}")
            print(f"      FOUND: {raw_cols}")

            # --- NUCLEAR PURGE ---
            # Keep only columns that match our whitelist (case-insensitive)
            cols_to_keep = [c for c in df.columns if str(c).upper().strip() in allowed_headers]
            df = df[cols_to_keep]
            print(f"      🛡️  REMAINING AFTER PURGE: {list(df.columns)}")

            # Find the target data column (looking for F0)
            target = None
            for col in df.columns:
                if 'F0' in str(col).upper():
                    target = col
                    break

            if not target:
                print(f"      ⚠️  No valid F0 target found in {list(df.columns)}. Skipping.")
                continue

            # --- DATA STANDARDIZATION ---
            temp_df = pd.DataFrame({
                'raw_date': df.iloc[:, 0],
                'value': pd.to_numeric(df[target], errors='coerce')
            }).dropna()

            # Date Parsing (Handles Excel 1967.1, 1967.2 style)
            def parse_period(val):
                try:
                    f_val = float(val)
                    year, rem = int(f_val), f_val - int(f_val)
                    # Quarters based on decimal remainder
                    q = 1 if rem < 0.15 else 2 if rem < 0.4 else 3 if rem < 0.65 else 4
                    return f"{year}Q{q}"
                except: return None

            temp_df['date'] = temp_df['raw_date'].apply(parse_period)
            
            # Collapse vintages by taking the LAST entry for each unique quarter
            final_df = temp_df.dropna(subset=['date']).groupby('date').last().reset_index()
            final_df = final_df[['date', 'value']].rename(columns={'value': var_name})

            # Save the clean file
            final_df.to_csv(os.path.join(output_dir, f"{var_name}.csv"), index=False)
            print(f"      ✅ SUCCESS: Saved {var_name}.csv")
                
        except Exception as e:
            print(f"      ❌ ERROR in sheet '{sheet}': {e}")

if __name__ == "__main__":
    # Ensure these paths match your container volume mapping
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')