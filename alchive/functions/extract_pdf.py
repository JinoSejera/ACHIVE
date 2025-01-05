import PyPDF2
from io import BytesIO

class ExtractPDF:
    @staticmethod
    def extract_pages(pdf_bytes:bytes) -> list[str]:
        try:
            # Create a list to hold the text of each page
            pages_text = []
            
            # Create a PyPDF2 PdfReader object from the downloaded PDF bytes
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
                
            # Iterate through each page in the PDF
            for page_number in range(len(pdf_reader.pages)):
                # Extract text from the page
                page = pdf_reader.pages[page_number]
                text = page.extract_text()
                pages_text.append(text.strip())
            
            return pages_text
        
        except Exception as e:
            print(e)