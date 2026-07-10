import re
import chromadb


class RAGPipeline:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collectionMda = self.client.get_or_create_collection(name="MD_A_Risk_Factors")

    def chunk_text(self, text: str, max_tokens=500, overlap_sentences=2):

        sentences = split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_tokens = len(sentence.split())

            if current_length + sentence_tokens > max_tokens and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = current_chunk[-overlap_sentences:]
                current_length = sum(len(s.split()) for s in current_chunk)

            current_chunk.append(sentence)
            current_length += sentence_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def ingest_section(self, cik, fiscal_year, section_name, text, filing_id):
        """Chunk a section's narrative text and upsert every chunk into ChromaDB.

        Idempotent: deterministic ids + upsert mean re-running the pipeline
        overwrites existing chunks instead of duplicating or crashing.
        """
        if not text or not text.strip():
            print(f"  [rag] skip empty section {section_name} (filing {filing_id})")
            return

        chunks = self.chunk_text(text)
        if not chunks:
            print(f"  [rag] no chunks produced for {section_name} (filing {filing_id})")
            return

        ids = [f"{filing_id}_{section_name}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "cik": cik,
                "fiscal_year": int(fiscal_year),
                "section_name": section_name,
                "filing_id": filing_id,
            }
            for _ in chunks
        ]

        self.collectionMda.upsert(
            documents=chunks,
            metadatas=metadatas,
            ids=ids,
        )
        print(f"  [rag] upserted {len(chunks)} chunks for {section_name} FY{fiscal_year} (filing {filing_id})")

    def query(self, query_text, where=None, n_results=3):
        """Convenience helper for manual verification / debugging."""
        return self.collectionMda.query(
            query_texts=[query_text],
            where=where,
            n_results=n_results,
        )


def split_into_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if s.strip()]