import pandas as pd
import os
import re
import sys

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor...")
    print(f"Reading from: {excel_path}")
    
    if not os.path.exists(excel_path):
        print(f"❌ CRITICAL: Excel file not found at {excel_path}")
        return

    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    
    for sheet in xls.sheet_names:
        if sheet.lower() in ['documentation', 'notes', 'summary', 'definitions']:
            continue
            
        # Read the sheet to find the header
        df = pd.read_excel(xls, sheet_name=sheet, header=None)
        
        date_row_index = None
        for i, row in df.iterrows():
            row_str = " ".join(row.astype(str))
            # Catch 2024Q1, 2024:Q1, or 2024-Q1
            if re.search(r'\d{4}[:\-]?Q\d', row_str):
                date_row_index = i
                break
        
        if date_row_index is None:
            continue

        # Process and save
        df = pd.read_excel(xls, sheet_name=sheet, skiprows=date_row_index)
        df.columns = [str(c).strip().replace(':', '') for c in df.columns]
        date_cols = [c for c in df.columns if re.search(r'\d{4}Q\d', c)]
        
        if date_cols:
            latest_data = df.iloc[-1][date_cols]
            final_df = pd.DataFrame(latest_data).reset_index()
            # Mapping specifically for FRB/US
            var_name = 'LUR' if sheet == 'UNEMP' else sheet
            final_df.columns = ['date', var_name]
            
            final_df['date'] = pd.PeriodIndex(final_df['date'], freq='Q')
            save_path = os.path.join(output_dir, f"{var_name.lower()}.csv")
            final_df.set_index('date').to_csv(save_path)
            print(f"✅ Saved: {var_name} -> {save_path}")

    print(f"🏁 Preprocessing Finished. Files in {output_dir}: {os.listdir(output_dir)}")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')