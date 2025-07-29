import shutil
from pathlib import Path
from PyPDF2 import PdfReader
from nltk.tokenize import sent_tokenize
from fastapi import UploadFile, HTTPException
from src.config import ALLOWED_FILE_EXTENSIONS, DOCS_FOLDER, CHUNK_SIZE_WORDS

class DocumentManager:
    def __init__(self, docs_folder=DOCS_FOLDER):
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

    def split_text_into_chunks(self, text, max_words=CHUNK_SIZE_WORDS):
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
        if not any(filename.endswith(ext) for ext in ALLOWED_FILE_EXTENSIONS):
            raise HTTPException(status_code=400, detail="Unsupported file type.")
        save_path = self.docs_folder / filename
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return save_path
