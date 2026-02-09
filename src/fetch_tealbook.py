import os
import requests
import pandas as pd

def fetch_tealbook_data():
    data_dir = "/home/spark/data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Use a session to persist headers and handle cookies automatically
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/tealbook-data-set',
        'Connection': 'keep-alive'
    })

    excel_url = "https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/tealbook/philadelphia_data_set.xlsx"
    local_xlsx = os.path.join(data_dir, "tealbook_raw.xlsx")
    output_csv = os.path.join(data_dir, "tealbook_unemployment.csv")
    
    print("📡 Fetching Excel Projections...")
    try:
        # Step 1: Hit the landing page first to establish a session
        session.get("https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/tealbook-data-set", timeout=10)
        
        # Step 2: Download the actual file
        r = session.get(excel_url, timeout=30)
        
        # Verify it's actually an Excel file (headers or content signature)
        if r.status_code == 200 and r.content.startswith(b'PK'):
            with open(local_xlsx, 'wb') as f:
                f.write(r.content)
            df = pd.read_excel(local_xlsx, sheet_name='RUC', engine='openpyxl')
            df.to_csv(output_csv, index=False)
            print(f"✅ CSV Generated: {output_csv}")
        else:
            print(f"❌ Blocked. Received Content-Type: {r.headers.get('Content-Type')}")
    except Exception as e:
        print(f"❌ Fetch Error: {e}")

if __name__ == "__main__":
    fetch_tealbook_data()