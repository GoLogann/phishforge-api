import os
import re
import unicodedata
import numpy as np
from typing import Dict, List
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, Range

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader


class DocumentProcessor:
    def __init__(self, chunk_size: int = 1024, chunk_overlap: int = 256):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        self.qdrant_client = QdrantClient("http://localhost:6333")

    def preprocess_text(self, text: str) -> str:
        """Limpa e normaliza o texto."""
        text = text.lower()
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        text = re.sub(r'[^\w\s.,!?-]', ' ', text)
        return " ".join(text.split())

    def retrieve_top_k(self, query_vector: np.ndarray, top_k: int = 4, filters: dict = None):
        """
        Recupera os top-k documentos mais relevantes com base na similaridade semântica e filtros opcionais.
        """
        conditions = []
        if filters:
            for field, value_range in filters.items():
                conditions.append(FieldCondition(
                    key=field,
                    range=Range(**value_range)
                ))

        query_filter = Filter(must=conditions) if conditions else None

        search_result = self.qdrant_client.search(
            collection_name="document_chunks",
            query_vector=query_vector,
            query_filter=query_filter,
            top=top_k
        )

        return [hit.payload for hit in search_result]

    def process_file(self, file_path: str) -> List[Dict]:
        """
        Método principal que carrega e divide um arquivo em chunks com base na sua extensão.
        """
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == ".pdf":
            loader = PyPDFLoader(file_path)
        elif file_extension in [".md", ".txt"]:
            loader = TextLoader(file_path, encoding='utf-8')
        else:
            print(f"⚠️  Tipo de arquivo não suportado: {file_extension}. Pulando.")
            return []

        documents = loader.load()
        chunks = self._create_small_to_big_chunks(documents, file_path)

        # Indexar os chunks no Qdrant
        for chunk in chunks:
            self.qdrant_client.upsert(
                collection_name="document_chunks",
                points=[{
                    "id": chunk["metadata"]["chunk_id"],
                    "vector": self._embed_text(chunk["child_text"]),
                    "payload": chunk["metadata"]
                }]
            )

        return chunks

    def _embed_text(self, text: str) -> np.ndarray:
        """
        Gera o embedding para um texto usando o modelo de embedding configurado.
        """
        # Simulação de embedding; substitua pela chamada ao modelo real
        return np.random.rand(1536)

    def _create_small_to_big_chunks(self, documents: List[Document], file_path: str) -> List[Dict]:
        """
        Processa uma lista de documentos carregados e os divide em chunks "Small-to-Big".
        """
        chunks_with_metadata = []
        file_name = os.path.basename(file_path)

        for doc in documents:
            parent_content = self.preprocess_text(doc.page_content)
            child_chunks = self.splitter.split_text(parent_content)

            # Para PDFs, doc.metadata['page'] existe. Para .md/.txt, definimos como 1.
            page_number = doc.metadata.get("page", 0) + 1

            for idx, child_chunk in enumerate(child_chunks):
                chunks_with_metadata.append({
                    "child_text": child_chunk,       # O texto "filho" a ser embedado
                    "parent_text": parent_content,   # O texto "pai" para o contexto
                    "metadata": {
                        "source": file_name,
                        "page": page_number,
                        "chunk_id": f"page_{page_number}_chunk_{idx}"
                    }
                })
        return chunks_with_metadata