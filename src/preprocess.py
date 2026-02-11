import pandas as pd
import os
import shutil

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor (Build #685 Direct Indexing)... ")
    
    # 1. CLEAN SWEEP
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print(f"❌ FATAL: Could not load Excel file: {e}")
        return

    # MAPPING: {Sheet Name: (Variable Name, Column Index)}
    # We use index 1 because index 0 is almost always the date.
    config = {
        'unemp': ('adjlegrt', 1),
        'lur':   ('adjlegrt', 1),
        'gdp':   ('anngr', 1),
        'pce':   ('eco', 1)
    }
    
    for sheet in xls.sheet_names:
        s_clean = sheet.strip().lower()
        if s_clean not in config: continue 
            
        var_name, col_idx = config[s_clean]
        try:
            # We don't skiprows here so we can see the full structure
            df = pd.read_excel(xls, sheet_name=sheet)
            
            # --- DIRECT INDEX SELECTION ---
            # Column 0 = Dates, Column 1 = Data
            date_col = df.iloc[:, 0]
            data_col = df.iloc[:, col_idx]
            
            # Convert data to numeric and drop rows where either date or data is missing
            processed_df = pd.DataFrame({
                'date_raw': date_col,
                var_name: pd.to_numeric(data_col, errors='coerce')
            }).dropna()

            # --- QUARTERLY DATE PARSING ---
            def parse_period(val):
                try:
                    f_val = float(val)
                    year, rem = int(f_val), f_val - int(f_val)
                    q = 1 if rem < 0.1 else 2 if rem < 0.3 else 3 if rem < 0.6 else 4
                    return f"{year}Q{q}"
                except: return None

            processed_df['date'] = processed_df['date_raw'].apply(parse_period)
            
            # Deduplicate and Save
            final_df = processed_df.dropna(subset=['date', var_name])
            if not final_df.empty:
                final_df = final_df.groupby('date')[var_name].last().reset_index()
                final_df.to_csv(os.path.join(output_dir, f"{var_name}.csv"), index=False)
                print(f"   ✅ SUCCESS: Saved {var_name}.csv from Column {col_idx}")
                
        except Exception as e:
            print(f"   ❌ Error processing sheet '{sheet}': {e}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')