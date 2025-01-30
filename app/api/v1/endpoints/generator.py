from fastapi import APIRouter, HTTPException, Depends
from app.domain.services.embedding_service import EmbeddingService
from app.dto.query import QueryRequest
from app.infrastructure.qdrant.store import QdrantVectorStore
from app.infrastructure.sentence_transformers.embedding_client import SentenceTransformersEmbeddingClient

app = APIRouter()

def get_embedding_service() -> EmbeddingService:
    embedding_client = SentenceTransformersEmbeddingClient()
    return EmbeddingService(embedding_client)

def get_qdrant_vector_store() -> QdrantVectorStore:
    vector_store = QdrantVectorStore()
    return vector_store

@app.post("/api/v1/generate")
async def generate(
        request: QueryRequest,
        embedding_service: EmbeddingService = Depends(get_embedding_service),
        vector_store: QdrantVectorStore = Depends(get_qdrant_vector_store),
):
    try:
        query_embedding = embedding_service.embedding_client.embed("Hello, world!")

        vector_store.save(collection_name="testando_novo_repositorio", chunks=["Hello, world!"], chunk_embeddings=query_embedding)

        return {"query_embedding": query_embedding}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
