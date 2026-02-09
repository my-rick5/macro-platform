import pdfplumber

def scrape_add_factors(pdf_path):
    findings = []
    # Keywords the Fed staff uses when they "cheat" the model
    target_keywords = ["add-factor", "judgmental", "override", "adjusted", "intercept"]
    
    with pdfplumber.open(pdf_path) as pdf:
        # The 'Staff Review' is usually the first 15 pages
        for i, page in enumerate(pdf.pages[:15]):
            text = page.extract_text()
            if text:
                for line in text.split('\n'):
                    if any(key in line.lower() for key in target_keywords):
                        findings.append({"page": i+1, "text": line.strip()})
    return findings
