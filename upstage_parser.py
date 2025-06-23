import os
import requests
import json
from dotenv import load_dotenv
from PyPDF2 import PdfReader, PdfWriter

# Load environment variables from .env file
load_dotenv()

# The API key is loaded from the environment variable.
api_key = os.getenv("UPSTAGE_API_KEY")
if not api_key:
    raise ValueError("UPSTAGE_API_KEY environment variable is not set. Please create a .env file and set your API key.")

# Path to the PDF file
pdf_path = "data/1_1.pdf"
if not os.path.exists(pdf_path):
    raise FileNotFoundError(f"The file was not found at path: {pdf_path}")

pdf_reader = PdfReader(pdf_path)
num_pages = len(pdf_reader.pages)

url = "https://api.upstage.ai/v1/document-digitization"
headers = {"Authorization": f"Bearer {api_key}"}
data = {"ocr": "auto", "base64_encoding": "", "model": "document-parse", "output_formats": "['html', 'markdown']"}

if num_pages <= 100:
    files = {"document": open(pdf_path, "rb")}
    response = requests.post(url, headers=headers, files=files, data=data)
    
    print(response.json())

    with open("parser_output_1_1.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(response.json(), ensure_ascii=False, indent=4))
else:
    for i in range(0, num_pages, 100):
        pdf_writer = PdfWriter()
        start_page = i
        end_page = min(i + 100, num_pages)

        for page_num in range(start_page, end_page):
            pdf_writer.add_page(pdf_reader.pages[page_num])
        
        chunk_pdf_path = f"temp_chunk_{i//100 + 1}.pdf"
        with open(chunk_pdf_path, "wb") as chunk_pdf_file:
            pdf_writer.write(chunk_pdf_file)
        
        with open(chunk_pdf_path, "rb") as f:
            files = {"document": f}
            response = requests.post(url, headers=headers, files=files, data=data)

        print(f"Response for pages {start_page+1}-{end_page}:")
        print(response.json())

        output_filename = f"parser_output_full_book_{i//100 + 1}.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(json.dumps(response.json(), ensure_ascii=False, indent=4))
        
        os.remove(chunk_pdf_path)