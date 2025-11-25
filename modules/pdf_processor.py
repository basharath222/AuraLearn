import pdfplumber
import PyPDF2
import pandas as pd
import docx # NEW LIBRARY
import io

def extract_text_from_pdf(uploaded_file):
    """
    Extracts text from various file types (PDF, DOCX, TXT, CSV, XLSX, XML).
    Includes robust fallback for PDFs using pdfplumber and PyPDF2.
    """
    text = ""

    try:
        # 1. Handle PDF
        if uploaded_file.type == "application/pdf":
            # Try with pdfplumber first
            try:
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        content = page.extract_text()
                        if content:
                            text += content + "\n"
            except Exception as e:
                print(f"pdfplumber failed: {e}")

            # Fallback to PyPDF2 if text seems too short or empty
            if len(text.strip()) < 200:
                try:
                    uploaded_file.seek(0)  # Reset file pointer
                    reader = PyPDF2.PdfReader(uploaded_file)
                    for page in reader.pages:
                        content = page.extract_text()
                        if content:
                            text += content + "\n"
                except Exception as e:
                    return f"⚠️ Error reading PDF with fallback: {e}"
            
            return text.strip() if text.strip() else "⚠️ PDF scanned or empty."

        # 2. Handle DOCX (Word Documents) - NEW!
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            fullText = []
            for para in doc.paragraphs:
                fullText.append(para.text)
            return '\n'.join(fullText)

        # 3. Handle Text / Markdown
        elif uploaded_file.type in ["text/plain", "text/markdown"]:
            return uploaded_file.read().decode("utf-8")

        # 4. Handle CSV
        elif uploaded_file.type == "text/csv":
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)
            return df.to_string()

        # 5. Handle Excel
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file)
            return df.to_string()
        
        # 6. Handle XML
        elif uploaded_file.type in ["text/xml", "application/xml"]:
            return uploaded_file.read().decode("utf-8")

        else:
            return f"⚠️ Unsupported file type: {uploaded_file.type}. Please upload PDF, DOCX, TXT, CSV, or Excel."

    except Exception as e:
        return f"⚠️ Error processing file: {str(e)}"