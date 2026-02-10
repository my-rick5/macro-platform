import pandas as pd
import os

def clean_fed_excel(excel_path, output_dir):
    """
    Scans the Phil Fed 'Library', skips junk sheets, and 
    creates clean CSVs for the engine.
    """
    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    
    # List of sheets to skip (case-insensitive)
    skip_list = ['documentation', 'notes', 'summary', 'definitions']
    
    for sheet in xls.sheet_names:
        if sheet.lower() in skip_list:
            print(f"⏭️  Skipping non-data sheet: {sheet}")
            continue
            
        # Load sheet and check if it has content
        df = pd.read_excel(xls, sheet_name=sheet)
        if df.empty or df.dropna(how='all').empty:
            print(f"👻 Skipping empty sheet: {sheet}")
            continue

        print(f"⚡ Processing variable: {sheet}...")
        
        # 1. FIND THE DATA ROW: Phil Fed Row Format uses row-based publication dates.
        # We usually want the most recent row (the latest Tealbook publication).
        latest_data = df.iloc[-1]
        
        # 2. FILTER FOR DATES: Columns look like '1996Q1', '2024Q3', etc.
        # We use a regex to grab only the quarterly headers.
        quarterly_series = latest_data.filter(regex=r'\d{4}Q\d')
        
        if quarterly_series.empty:
            print(f"⚠️  No quarterly data found in sheet {sheet}. Skipping.")
            continue

        # 3. CONVERT TO MODEL FORMAT
        final_df = pd.DataFrame(quarterly_series).reset_index()
        final_df.columns = ['date', sheet] # Sheet name is usually the mnemonic (e.g. UNEMP)
        
        # FRB/US specific: UNEMP in Fed data must be renamed to LUR for the model
        if sheet == 'UNEMP': final_df.columns = ['date', 'LUR']

        # Set index and save
        final_df['date'] = pd.PeriodIndex(final_df['date'], freq='Q')
        final_df = final_df.set_index('date')
        
        csv_name = f"{sheet.lower()}.csv"
        final_df.to_csv(os.path.join(output_dir, csv_name))

    print(f"✅ Preprocessing complete. Data ready in {output_dir}")

if __name__ == "__main__":
    clean_fed_excel('/source_code/external_data/GBweb_Row_Format.xlsx', '/home/spark/data/processed')