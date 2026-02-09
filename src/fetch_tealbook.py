import os
import requests
import pandas as pd
import pdfplumber

def fetch_tealbook_data():
    data_dir = "/home/spark/data"
    pdf_dir = os.path.join(data_dir, "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Advanced headers to bypass "Access Denied" HTML blocks
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/tealbook-data-set',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    # 1. DOWNLOAD EXCEL (Quantitative Data)
    excel_url = "https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/tealbook/philadelphia_data_set.xlsx"
    local_xlsx = os.path.join(data_dir, "tealbook_raw.xlsx")
    output_csv = os.path.join(data_dir, "tealbook_unemployment.csv")
    
    print("📡 Fetching Excel Projections...")
    try:
        r = requests.get(excel_url, headers=headers, timeout=30)
        r.raise_for_status()
        
        # Guard against getting HTML instead of Excel
        if 'application/vnd.openxmlformats-officedocument' not in r.headers.get('Content-Type', ''):
            print(f"❌ Error: Received {r.headers.get('Content-Type')}. Fed is blocking the script.")
            return

        with open(local_xlsx, 'wb') as f:
            f.write(r.content)
        
        df = pd.read_excel(local_xlsx, sheet_name='RUC', engine='openpyxl')
        df.to_csv(output_csv, index=False)
        print(f"✅ CSV Generated: {output_csv}")
    except Exception as e:
        print(f"❌ Excel Fetch Failed: {e}")

    # 2. DOWNLOAD & PARSE PDF (Qualitative Narrative)
    test_year = 2004 
    pdf_url = f"https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/tealbook/pdfs/{test_year}/tealbook-a-{test_year}.pdf"
    local_pdf = os.path.join(pdf_dir, f"tealbook_a_{test_year}.pdf")
    
    print(f"📄 Fetching {test_year} Narrative PDF...")
    try:
        r = requests.get(pdf_url, headers=headers, timeout=30)
        r.raise_for_status()
        
        if 'application/pdf' not in r.headers.get('Content-Type', ''):
             raise ValueError("URL did not return a valid PDF. Check year or Fed access.")

        with open(local_pdf, 'wb') as f:
            f.write(r.content)
            
        judgment_lines = []
        keywords = ["add-factor", "judgmental", "override", "adjusted", "intercept"]
        
        with pdfplumber.open(local_pdf) as pdf:
            # Tealbook A usually contains the meat in the first 15 pages
            for i, page in enumerate(pdf.pages[:15]):
                text = page.extract_text()
                if text:
                    for line in text.split('\n'):
                        if any(k in line.lower() for k in keywords):
                            judgment_lines.append(f"Page {i+1}: {line.strip()}")
        
        log_path = os.path.join(data_dir, f"add_factors_{test_year}.txt")
        with open(log_path, 'w') as f:
            f.write("\n".join(judgment_lines))
        print(f"✅ Scraped {len(judgment_lines)} staff judgment lines.")
            
    except Exception as e:
        print(f"❌ PDF Scraping Failed: {e}")

    # Cleanup large Excel file to save Jenkins space
    if os.path.exists(local_xlsx): os.remove(local_xlsx)

if __name__ == "__main__":
    fetch_tealbook_data()