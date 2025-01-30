from app.domain.services.document_processor import DocumentProcessor
from app.domain.services.embedding_service import EmbeddingService
from app.infrastructure.qdrant.store import QdrantVectorStore
from app.infrastructure.sentence_transformers.embedding_client import SentenceTransformersEmbeddingClient

if __name__ == "__main__":
    vector_store = QdrantVectorStore()
    processor = DocumentProcessor()

    embedding_service = EmbeddingService(embedding_client=SentenceTransformersEmbeddingClient())

    document_text = processor.preprocess_file_rag("data/Phishing-Dark-Waters-The-Offensive-and-Defensive-Sides-of-Malicious-Emails.pdf")
    chunks = processor.process_document_data(document_text)

    chunk_embeddings = embedding_service.generate_embeddings(chunks)

    vector_store.save(
        collection_name="phishing_book",
        chunks=chunks,
        chunk_embeddings=chunk_embeddings
    )