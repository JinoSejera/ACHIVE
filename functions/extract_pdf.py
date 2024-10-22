import PyPDF2


class ExtractPDF:
    @staticmethod
    def extract_pages(file_path:str) -> list[str]:
        try:
            # Create a list to hold the text of each page
            pages_text = []
            
            # Open the PDF file
            with open(file_path, 'rb') as file:
                # Create a PdfFileReader object
                reader = PyPDF2.PdfReader(file)
                
                # Iterate through each page in the PDF
                for page_number in range(len(reader.pages)):
                    # Extract text from the page
                    page = reader.pages[page_number]
                    text = page.extract_text()
                    pages_text.append(text.strip())
            
            return pages_text
        except Exception as e:
            print(e)