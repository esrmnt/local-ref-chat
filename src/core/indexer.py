from sentence_transformers import SentenceTransformer
import numpy as np

class Indexer:
    def __init__(self, embedding_model_name="all-MiniLM-L6-v2"):
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.documents = {}  # doc_id: full_text
        self.index = {}      # chunk_id: {"text", "doc_id", "filename", "chunk_index", "embedding"}

    def rebuild(self, doc_manager):
        doc_id = 0
        chunk_id = 0
        self.documents.clear()
        self.index.clear()

        if not doc_manager.docs_folder.exists():
            print("Docs folder not found, skipping indexing.")
            return

        for file_path in doc_manager.docs_folder.iterdir():
            if file_path.suffix.lower() == ".pdf":
                try:
                    text = doc_manager.extract_text_from_pdf(file_path)
                except Exception as e:
                    print(f"Failed to read PDF {file_path.name}: {e}")
                    continue
            elif file_path.suffix.lower() == ".txt":
                try:
                    text = doc_manager.extract_text_from_txt(file_path)
                except Exception as e:
                    print(f"Failed to read TXT {file_path.name}: {e}")
                    continue
            else:
                continue

            self.documents[doc_id] = text

            chunks = doc_manager.split_text_into_chunks(text)
            for i, chunk_text in enumerate(chunks):
                embedding = self.embedding_model.encode(chunk_text)
                self.index[chunk_id] = {
                    "text": chunk_text,
                    "doc_id": doc_id,
                    "filename": file_path.name,
                    "chunk_index": i,
                    "embedding": embedding
                }
                chunk_id += 1
            doc_id += 1

        print(f"Indexed {len(self.documents)} documents into {len(self.index)} chunks.")

    def keyword_search(self, query):
        results = []
        for chunk in self.index.values():
            if query.lower() in chunk["text"].lower():
                results.append({
                    "filename": chunk["filename"],
                    "chunk_index": chunk["chunk_index"],
                    "text_snippet": chunk["text"][:250] + ("..." if len(chunk["text"]) > 250 else "")
                })
        return results

    def semantic_search(self, query, top_k=5):
        query_emb = self.embedding_model.encode(query)
        rank = []
        for chunk in self.index.values():
            emb = chunk["embedding"]
            sim = np.dot(emb, query_emb) / (np.linalg.norm(emb) * np.linalg.norm(query_emb))
            rank.append((sim, chunk))
        rank.sort(key=lambda x: x[0], reverse=True)
        results = [
            {
                "filename": chunk["filename"],
                "chunk_index": chunk["chunk_index"],
                "similarity": float(score),
                "text_snippet": chunk["text"][:250] + ("..." if len(chunk["text"]) > 250 else "")
            }
            for score, chunk in rank[:top_k]
        ]
        return results
