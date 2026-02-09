import os
import requests
import pandas as pd
import pdfplumber

def fetch_tealbook_data():
    # Paths & Setup
    data_dir = "/home/spark/data" if os.path.exists("/home/spark") else "data"
    pdf_dir = os.path.join(data_dir, "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    
    # 1. DOWNLOAD EXCEL (Forecast Outputs)
    excel_url = "https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/tealbook/philadelphia_data_set.xlsx"
    local_xlsx = os.path.join(data_dir, "tealbook_raw.xlsx")
    output_csv = os.path.join(data_dir, "tealbook_unemployment.csv")
    
    print("📡 Fetching Excel Projections...")
    try:
        r = requests.get(excel_url, timeout=30)
        r.raise_for_status()
        with open(local_xlsx, 'wb') as f: f.write(r.content)
        
        df = pd.read_excel(local_xlsx, sheet_name='RUC', engine='openpyxl')
        df.to_csv(output_csv, index=False)
        print(f"✅ Excel saved: {output_csv}")
    except Exception as e:
        print(f"❌ Excel Fetch Failed: {e}")

    # 2. DOWNLOAD & PARSE NARRATIVE PDF (Staff Judgment)
    # Example for 2004 (adjust loop or param as needed for your backtest)
    test_year = 2004 
    pdf_url = f"https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/tealbook/pdfs/{test_year}/tealbook-a-{test_year}.pdf"
    local_pdf = os.path.join(pdf_dir, f"tealbook_a_{test_year}.pdf")
    
    print(f"📄 Fetching {test_year} Narrative PDF...")
    try:
        r = requests.get(pdf_url, timeout=30)
        if r.status_code == 200:
            with open(local_pdf, 'wb') as f: f.write(r.content)
            
            # Scrape for Add-Factors
            judgment_lines = []
            keywords = ["add-factor", "judgmental", "override", "adjusted", "intercept"]
            
            with pdfplumber.open(local_pdf) as pdf:
                # Scan first 15 pages where 'Staff Review' usually lives
                for i, page in enumerate(pdf.pages[:15]):
                    text = page.extract_text()
                    if text:
                        for line in text.split('\n'):
                            if any(k in line.lower() for k in keywords):
                                judgment_lines.append(f"P{i+1}: {line.strip()}")
            
            # Save findings for XGBoost feature extraction
            log_path = os.path.join(data_dir, f"add_factors_{test_year}.txt")
            with open(log_path, 'w') as f:
                f.write("\n".join(judgment_lines))
            print(f"✅ Found {len(judgment_lines)} potential judgmental overrides in PDF.")
        else:
            print(f"⚠️ PDF not found for {test_year} (Status {r.status_code})")
            
    except Exception as e:
        print(f"❌ PDF Scraping Failed: {e}")

    # CLEANUP: Remove large Excel (keep CSV and small PDF)
    if os.path.exists(local_xlsx):
        os.remove(local_xlsx)

if __name__ == "__main__":
    fetch_tealbook_data()