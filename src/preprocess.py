import pandas as pd
import os
import datetime

def clean_fed_excel(excel_path, output_dir):
    # Generation timestamp for audit trail
    now = datetime.datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    file_tag = now.strftime("%Y%m%d_%H%M%S")
    
    print(f"🎬 Starting Preprocessor (Build #721 - Timestamped Audit)...")
    print(f"   🕒 Run Time: {timestamp_str}")
    
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
    
    # SYNCED MAPPING
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
            if cols_to_keep:
                df = df[cols_to_keep]

            # --- STRICTER TARGET SELECTION ---
            target = None
            for col in df.columns:
                c_upper = str(col).upper().strip()
                # Must have F0, but cannot be a Date/Period/Stamp column
                if 'F0' in c_upper and all(x not in c_upper for x in ['DATE', 'PERIOD', 'STAMP']):
                    target = col
                    break

            if not target:
                print(f"      ⚠️ WARNING: No valid F0 value column in '{sheet}'. Skipping.")
                continue

            print(f"      🎯 TARGET FOUND: In '{sheet}', selected column '{target}'")

            # --- VALUE GUARD ---
            temp_df = pd.DataFrame({
                'raw_date': df.iloc[:, 0],
                'value': pd.to_numeric(df[target], errors='coerce')
            })

            # Filter out large integers (dates like 20100310)
            temp_df = temp_df[temp_df['value'] < 1000].dropna()

            if temp_df.empty:
                print(f"      ❌ REJECTED: Column '{target}' contained only dates or invalid numbers.")
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

            # --- TIMESTAMP INJECTION ---
            # Adding this column ensures you can verify data freshness inside the CSV
            final_df['processed_at'] = timestamp_str

            # --- THE TOTAL TAKEOVER ---
            possible_dirs = [
                output_dir,
                "/home/spark/data",
                "/home/spark/external_data",
                "/home/spark"
            ]
            
            for d in possible_dirs:
                if os.path.exists(d):
                    # We save the standard name for the engine, but log the overwrite
                    target_path = os.path.join(d, f"{var_name}.csv")
                    final_df.to_csv(target_path, index=False)
                    print(f"      🚀 OVERWROTE: {target_path}")
            
            # --- AUDIT PREVIEW ---
            print(f"      📊 DATA PREVIEW FOR {var_name} (Build Time: {timestamp_str}):")
            print(final_df.head(2).to_string(index=False))
            print("-" * 40)
                
        except Exception as e:
            print(f"      ❌ ERROR in sheet '{sheet}': {e}")

if __name__ == "__main__":
    clean_fed_excel('library.xlsx', './processed')