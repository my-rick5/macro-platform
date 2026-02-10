import pandas as pd
import os
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor...")
    if not os.path.exists(excel_path):
        print(f"❌ CRITICAL: Excel file not found at {excel_path}")
        return

    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    
    for sheet in xls.sheet_names:
        if sheet.lower() in ['documentation', 'notes', 'summary', 'definitions']:
            continue
            
        # Read first 50 rows to find the date headers
        df_raw = pd.read_excel(xls, sheet_name=sheet, header=None, nrows=50)
        
        date_row_index = None
        for i, row in df_raw.iterrows():
            row_str = " ".join(row.astype(str))
            # Regex catches: 2024Q1, 2024:Q1, 2024-Q1, or 2024 Q1
            if re.search(r'\d{4}[ \-:]?Q\d', row_str):
                date_row_index = i
                break
        
        if date_row_index is None:
            continue

        # Load full data starting from the date row
        df = pd.read_excel(xls, sheet_name=sheet, skiprows=date_row_index)
        
        # Clean column names to find dates
        df.columns = [str(c).strip().replace(':', '') for c in df.columns]
        date_cols = [c for c in df.columns if re.search(r'\d{4}Q\d', c)]
        
        if date_cols:
            # We take the LAST row (most recent vintage)
            latest_data = df.iloc[-1][date_cols]
            
            # Map variable names for the FRB/US Engine
            var_name = 'LUR' if sheet.upper() == 'UNEMP' else sheet.upper()
            
            final_df = pd.DataFrame(latest_data).reset_index()
            final_df.columns = ['date', var_name]
            
            # Standardize date format to 2024Q1 string for PeriodIndex
            final_df['date'] = final_df['date'].str.replace(r'[:\- ]', '', regex=True)
            final_df['date'] = pd.PeriodIndex(final_df['date'], freq='Q')
            
            save_path = os.path.join(output_dir, f"{var_name.lower()}.csv")
            final_df.set_index('date').sort_index().to_csv(save_path)
            print(f"✅ Variable Processed: {var_name}")

    print(f"🏁 Finished. Found {len(os.listdir(output_dir))} variables.")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')