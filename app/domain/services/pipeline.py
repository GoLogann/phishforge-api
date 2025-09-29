import glob
import os
from app.domain.services.document_processor import DocumentProcessor
from app.infra.qdrant.store import QdrantVectorStore

class IngestionPipeline:
    def __init__(self, processor: DocumentProcessor, vector_store: QdrantVectorStore):
        self.processor = processor
        self.vector_store = vector_store

    def ingest_pdfs_to_qdrant(self, data_dir: str = "data/articles", collection_name: str = "phishing_articles"):
        pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
        if not pdf_files:
            print("⚠️ Nenhum PDF encontrado em", data_dir)
            return

        for pdf_path in pdf_files:
            print(f"📄 Processando {pdf_path}...")
            chunks = self.processor.load_and_chunk_pdf(pdf_path)
            self.vector_store.save(collection_name, chunks)
            print(f"✅ {len(chunks)} chunks inseridos no Qdrant (coleção: {collection_name})")

        print("🚀 Pipeline concluído!")
