import pandas as pd
import os
import shutil

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #701 Nuclear Option)... ")
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"❌ FATAL: Could not load Excel file: {e}")
        return

    # THE WHITE LIST: Only these headers are allowed to exist
    allowed_headers = ['DATE', 'UNEMPF0', 'REALGDPF0', 'PCEF0', 'LURF0']
    mapping = {'unemp': 'adjlegrt', 'lur': 'adjlegrt', 'gdp': 'anngr', 'pce': 'eco'}
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in mapping: continue 
            
        var_name = mapping[s_clean]
        try:
            df = pd.read_excel(xls, sheet_name=sheet)

            # --- THE NUCLEAR PURGE ---
            # Drop every column that is not in our White List
            cols_to_keep = [c for c in df.columns if str(c).upper().strip() in allowed_headers]
            cols_to_kill = [c for c in df.columns if c not in cols_to_keep]
            
            df = df[cols_to_keep]
            print(f"   ☢️ Purged unknown columns: {cols_to_kill}")

            # Re-identify our target now that the junk is gone
            target_header = None
            possible_targets = ['UNEMPF0', 'LURF0', 'REALGDPF0', 'PCEF0']
            for t in possible_targets:
                if t in df.columns:
                    target_header = t
                    break

            if not target_header:
                print(f"   ⚠️ Skipping '{sheet}': No white-listed target found.")
                continue

            # --- DEDUPLICATION ---
            temp_df = pd.DataFrame({
                'raw_date': df.iloc[:, 0],
                'value': pd.to_numeric(df[target_header], errors='coerce')
            }).dropna()

            def parse_period(val):
                try:
                    f_val = float(val)
                    year, rem = int(f_val), f_val - int(f_val)
                    q = 1 if rem < 0.15 else 2 if rem < 0.4 else 3 if rem < 0.65 else 4
                    return f"{year}Q{q}"
                except: return None

            temp_df['date'] = temp_df['raw_date'].apply(parse_period)
            
            # Group by Quarter and take the LAST entry (latest vintage)
            final_df = temp_df.dropna(subset=['date']).groupby('date').last().reset_index()
            final_df = final_df[['date', 'value']].rename(columns={'value': var_name})

            final_df.to_csv(os.path.join(output_dir, f"{var_name}.csv"), index=False)
            print(f"   ✅ SUCCESS: Saved {var_name}.csv using {target_header}")
                
        except Exception as e:
            print(f"   ❌ Error processing sheet '{sheet}': {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')