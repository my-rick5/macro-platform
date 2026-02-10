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
            
        print(f"🔎 Processing Sheet: {sheet}")
        # Read sheet - row 1 (index 1) was identified as the header in your logs
        df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
        
        if df.empty:
            continue

        # 1. Standardize the first column to be our 'date' column
        # Greenbook files usually have the date in the first column (Index 0)
        df.rename(columns={df.columns[0]: 'date'}, inplace=True)
        
        # 2. Identify the variable name
        # If the sheet is 'UNEMP', the model expects 'LUR'
        var_name = 'LUR' if 'unemp' in sheet.lower() else sheet.upper()
        
        # 3. Clean the Date column
        # Convert 1995:1 or 1995.1 or 1995Q1 to 1995Q1
        def standardize_date(val):
            s = str(val).strip()
            # Replace common delimiters with 'Q'
            s = re.sub(r'[:.\- ]', 'Q', s)
            # Ensure it matches YYYYQ#
            match = re.search(r'(\d{4})Q(\d)', s)
            if match:
                return f"{match.group(1)}Q{match.group(2)}"
            return None

        df['date'] = df['date'].apply(standardize_date)
        df = df.dropna(subset=['date'])

        # 4. Extract the data column
        # Usually, the 'latest' data is the LAST column in these row-format files
        # because new vintages are added as new columns.
        if len(df.columns) > 1:
            # Take the date column and the very last column (latest vintage)
            final_df = df[['date', df.columns[-1]]].copy()
            final_df.columns = ['date', var_name]
            
            try:
                # Convert to PeriodIndex for pyfrbus compatibility
                final_df['date'] = pd.PeriodIndex(final_df['date'], freq='Q')
                save_path = os.path.join(output_dir, f"{var_name.lower()}.csv")
                final_df.set_index('date').sort_index().to_csv(save_path)
                print(f"   ✅ Saved {var_name} with {len(final_df)} observations")
            except Exception as e:
                print(f"   ❌ Date conversion error in {sheet}: {e}")

    print(f"🏁 Finished. Found {len(os.listdir(output_dir))} variables.")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')