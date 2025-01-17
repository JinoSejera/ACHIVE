from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import PyPDF2
from io import BytesIO

app = FastAPI()

# Request model for the input data
class PDFLink(BaseModel):
    pdf_url: str


# Helper function to download the PDF from the URL
def download_pdf(url: str) -> bytes:
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to download PDF")
    return response.content


# Helper function to extract the first paragraph from the PDF
def extract_first_paragraph(pdf_content: bytes) -> str:
    # Open the PDF with PyPDF2
    pdf_file = BytesIO(pdf_content)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    # Extract text from the first page
    page = pdf_reader.pages[0]
    text = page.extract_text()

    # Split the text into paragraphs by new lines
    paragraphs = text.split("\n")
    
    # Find the first non-empty paragraph
    for paragraph in paragraphs:
        if paragraph.strip():
            return paragraph.strip()

    return "No text found in the PDF"


# FastAPI endpoint to handle the request
@app.post("/extract-paragraph/")
async def extract_paragraph(data: PDFLink):
    try:
        # Download the PDF content from the URL
        pdf_content = download_pdf(data.pdf_url)
        
        # Extract the first paragraph from the PDF content
        first_paragraph = extract_first_paragraph(pdf_content)
        
        return {"first_paragraph": first_paragraph}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

