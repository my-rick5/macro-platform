import pandas as pd
import os
import re

def clean_fed_excel(excel_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    
    skip_list = ['documentation', 'notes', 'summary', 'definitions']
    
    for sheet in xls.sheet_names:
        if sheet.lower() in skip_list:
            continue
            
        df = pd.read_excel(xls, sheet_name=sheet)
        
        # --- NEW ROBUST DATE DETECTION ---
        # Convert all column headers to strings and clean them
        df.columns = [str(c).strip().replace(':', '') for c in df.columns]
        
        # Look for columns matching YYYYQX (e.g., 2024Q3)
        date_cols = [c for c in df.columns if re.search(r'\d{4}Q\d', c)]
        
        if not date_cols:
            print(f"❌ Could not find quarterly columns in {sheet}. Found: {df.columns[:5]}")
            continue

        print(f"⚡ Processing variable: {sheet}...")
        
        # Grab the latest release (last row) and only the date columns
        latest_data = df.iloc[-1][date_cols]
        
        # Convert to a clean series
        final_df = pd.DataFrame(latest_data).reset_index()
        final_df.columns = ['date', sheet]
        
        # Model specific renaming
        if sheet == 'UNEMP': final_df.columns = ['date', 'LUR']

        final_df['date'] = pd.PeriodIndex(final_df['date'], freq='Q')
        final_df = final_df.set_index('date')
        
        csv_name = f"{sheet.lower()}.csv"
        final_df.to_csv(os.path.join(output_dir, csv_name))

    print(f"✅ Preprocessing complete.")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')