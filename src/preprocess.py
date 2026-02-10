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
            
        # 1. Read WITHOUT a header initially to find where the dates are
        df = pd.read_excel(xls, sheet_name=sheet, header=None)
        
        # 2. Find the row that contains the quarterly dates (e.g., '2024Q1')
        date_row_index = None
        for i, row in df.iterrows():
            if row.astype(str).str.contains(r'\d{4}Q\d').any():
                date_row_index = i
                break
        
        if date_row_index is None:
            print(f"❌ No date row found in {sheet}. Skipping.")
            continue

        # 3. Re-read the sheet starting from that date row
        df = pd.read_excel(xls, sheet_name=sheet, skiprows=date_row_index)
        
        # 4. Clean column names
        df.columns = [str(c).strip().replace(':', '') for c in df.columns]
        date_cols = [c for c in df.columns if re.search(r'\d{4}Q\d', c)]
        
        if not date_cols:
            print(f"❌ Failed second-pass column detection in {sheet}.")
            continue

        print(f"⚡ Found data in {sheet}. Processing latest release...")
        
        # 5. Extract latest release (last row)
        latest_data = df.iloc[-1][date_cols]
        
        # 6. Model specific renaming
        final_df = pd.DataFrame(latest_data).reset_index()
        final_df.columns = ['date', sheet]
        if sheet == 'UNEMP': final_df.columns = ['date', 'LUR']

        # 7. Final Formatting
        final_df['date'] = pd.PeriodIndex(final_df['date'], freq='Q')
        final_df = final_df.set_index('date')
        
        final_df.to_csv(os.path.join(output_dir, f"{sheet.lower()}.csv"))

    print(f"✅ Preprocessing complete.")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')