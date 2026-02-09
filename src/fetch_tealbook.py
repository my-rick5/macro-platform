import os
import requests
import pandas as pd
import pdfplumber

def fetch_tealbook_data():
    data_dir = "/home/spark/data"
    pdf_dir = os.path.join(data_dir, "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Headers to bypass bot detection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/tealbook-data-set'
    }

    # 1. Download Excel Data
    excel_url = "https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/tealbook/philadelphia_data_set.xlsx"
    local_xlsx = os.path.join(data_dir, "tealbook_raw.xlsx")
    output_csv = os.path.join(data_dir, "tealbook_unemployment.csv")
    
    print("📡 Fetching Excel Projections...")
    try:
        r = requests.get(excel_url, headers=headers, timeout=30)
        r.raise_for_status()
        
        if 'application/' in r.headers.get('Content-Type', ''):
            with open(local_xlsx, 'wb') as f:
                f.write(r.content)
            
            # Read and convert to CSV
            df = pd.read_excel(local_xlsx, sheet_name='RUC', engine='openpyxl')
            df.to_csv(output_csv, index=False)
            print(f"✅ Data saved to {output_csv}")
        else:
            print(f"❌ Blocked: Received {r.headers.get('Content-Type')}")
    except Exception as e:
        print(f"❌ Excel Error: {e}")

    # 2. Download and Parse Narrative PDF
    # (Example year 2004 - this can be parameterized later)
    test_year = 2004
    pdf_url = f"https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/tealbook/pdfs/{test_year}/tealbook-a-{test_year}.pdf"
    local_pdf = os.path.join(pdf_dir, f"tealbook_{test_year}.pdf")
    
    print(f"📄 Fetching {test_year} Narrative PDF...")
    try:
        r = requests.get(pdf_url, headers=headers, timeout=30)
        r.raise_for_status()
        
        with open(local_pdf, 'wb') as f:
            f.write(r.content)
            
        # Extract staff judgments
        with pdfplumber.open(local_pdf) as pdf:
            judgments = []
            for page in pdf.pages[:15]:
                text = page.extract_text()
                if text:
                    for line in text.split('\n'):
                        if "judgment" in line.lower() or "override" in line.lower():
                            judgments.append(line.strip())
                            
        with open(os.path.join(data_dir, f"add_factors_{test_year}.txt"), 'w') as f:
            f.write("\n".join(judgments))
        print("✅ Staff judgments extracted.")
    except Exception as e:
        print(f"❌ PDF Error: {e}")

    if os.path.exists(local_xlsx): os.remove(local_xlsx)

if __name__ == "__main__":
    fetch_tealbook_data()