import os
import pandas as pd

def fetch_and_verify_macro_data():
    # 1. SETUP: Define paths relative to the project root (/home/spark)
    local_xlsx = "library.xlsx" 
    output_csv = "data/tealbook_full_x.csv"
    
    # Ensure the output directory exists
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(local_xlsx):
        print(f"❌ ERROR: Source file not found at {os.path.abspath(local_xlsx)}")
        return

    # 2. DISCOVERY: Load workbook to see actual sheet names
    try:
        xl = pd.ExcelFile(local_xlsx)
        available_sheets = xl.sheet_names
        print(f"📋 Workbook Sheets Found: {available_sheets}")
    except Exception as e:
        print(f"❌ Failed to open Excel file: {e}")
        return

    # Mapping internal keys to possible sheet names in Philly Fed files
    target_mapping = {
        'unemp_x': ['UNEMP', 'unemp', 'RUC'],
        'gdp_growth_x': ['gRGDP', 'grgdp'],
        'pce_inf_x': ['gPPCE', 'gppce']
    }

    final_df = pd.DataFrame()

    # 3. EXTRACTION LOOP
    for var_name, possible_sheets in target_mapping.items():
        # Find which sheet exists in this workbook
        sheet = next((s for s in possible_sheets if s in available_sheets), None)
        
        if not sheet:
            print(f"⚠️  Skipping {var_name}: No matching sheet found in {available_sheets}")
            continue

        try:
            # Read sheet (headers are on row 0)
            df = pd.read_excel(xl, sheet_name=sheet)
            
            # Standardize column names (remove whitespace)
            df.columns = [str(c).strip() for c in df.columns]
            
            # Find 'DATE' column (case-insensitive)
            date_col = next((c for c in df.columns if c.upper() == 'DATE'), None)
            
            # Find Value column (the first column that isn't the Date)
            val_col = next((c for c in df.columns if c != date_col), None)

            if date_col and val_col:
                print(f"✅ Processing {sheet}: Using '{date_col}' and '{val_col}'")
                
                # Create temp dataframe
                temp = df[[date_col, val_col]].copy()
                temp.columns = ['date', var_name]
                
                # Clean Data: Convert to datetime and drop NaNs
                temp['date'] = pd.to_datetime(temp['date'], errors='coerce')
                temp = temp.dropna(subset=['date'])
                
                # --- CRITICAL: FIX ROW BLOAT ---
                # Philadelphia Fed files contain multiple vintages per date.
                # Sort by date and keep only the most recent entry per quarter.
                temp = temp.sort_values('date').drop_duplicates('date', keep='last')
                
                # Merge into master dataframe
                if final_df.empty:
                    final_df = temp
                else:
                    final_df = pd.merge(final_df, temp, on='date', how='outer')
            else:
                print(f"⚠️  Sheet {sheet} is missing required columns. Found: {list(df.columns)}")

        except Exception as e:
            print(f"❌ Failed to process sheet {sheet}: {e}")

    # 4. SAVE & VERIFY
    if final_df.empty:
        print("❌ CRITICAL: Final merged dataset is empty.")
        return

    # Final sort and save to CSV
    final_df.sort_values('date', inplace=True)
    final_df.to_csv(output_csv, index=False)
    
    print(f"\n✨ SUCCESS: Merged data saved to {output_csv}")
    print(f"📊 Final Clean Count: {len(final_df)} rows (down from ~45k)")

if __name__ == "__main__":
    fetch_and_verify_macro_data()