"""Extract text from $100M Leads PDF for analysis."""
from pypdf import PdfReader
import os

pdf_path = r'c:/Users/guerr/Downloads/$100m Everything/100M LEADS Alex Hormozi.pdf'
out_path = r'C:/Users/guerr/Documents/drozq.com/scripts/leads_text.txt'

reader = PdfReader(pdf_path)
print(f"Total pages: {len(reader.pages)}")

with open(out_path, 'w', encoding='utf-8') as f:
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ''
        f.write(f"\n\n===== PAGE {i+1} =====\n\n")
        f.write(text)
        if (i+1) % 50 == 0:
            print(f"Processed page {i+1}")

print(f"Done. Output size: {os.path.getsize(out_path):,} bytes")
