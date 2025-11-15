import pdfplumber
import PyPDF2

def extract_text_from_pdf(pdf_file):
    """
    Extract text content from a PDF using pdfplumber (primary)
    and PyPDF2 (fallback). Handles both uploaded files and file paths.
    """
    text = ""

    try:
        # Support both file uploads (Streamlit UploadedFile) and paths
        pdf_path = pdf_file if isinstance(pdf_file, str) else pdf_file.name

        # Try with pdfplumber first
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
    except Exception as e:
        print(f"pdfplumber failed: {e}")

    # Fallback if text seems too short
    if len(text.strip()) < 200:
        try:
            pdf_file.seek(0)  # Reset file pointer
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content
        except Exception as e:
            text += f"\nError with PyPDF2: {e}"

    return text.strip() if text else "⚠️ No readable text found in PDF."
