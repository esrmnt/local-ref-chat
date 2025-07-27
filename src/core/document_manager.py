from pathlib import Path
import shutil
from fastapi import UploadFile, HTTPException
from nltk.tokenize import sent_tokenize
from PyPDF2 import PdfReader

class DocumentManager:
    def __init__(self, docs_folder="docs"):
        self.docs_folder = Path(docs_folder)
        self.docs_folder.mkdir(parents=True, exist_ok=True)

    def extract_text_from_pdf(self, pdf_path):
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    def extract_text_from_txt(self, txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read()

    def split_text_into_chunks(self, text, max_words=500):
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        words_in_chunk = 0
        for sentence in sentences:
            words = sentence.split()
            if words_in_chunk + len(words) > max_words:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                words_in_chunk = 0
            current_chunk.append(sentence)
            words_in_chunk += len(words)
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    def save_uploaded_file(self, file: UploadFile):
        filename = file.filename
        if not (filename.endswith(".pdf") or filename.endswith(".txt")):
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")
        save_path = self.docs_folder / filename
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return save_path
