import json

from fastapi import APIRouter, HTTPException, Depends

from app.domain.services.embedding_service import EmbeddingService
from app.domain.services.response_generator import ResponseGenerator
from app.domain.models.phishing_email import PhishingEmail
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

def get_response_generator() -> ResponseGenerator:
    return ResponseGenerator()

@app.post("/api/v1/generate")
async def generate(
        request: QueryRequest,
        response_generator: ResponseGenerator = Depends(get_response_generator)
):
    try:
        phishing_example = await response_generator.generate_response(
            difficulty="dificil",
            context=request.context
        )

        if phishing_example and isinstance(phishing_example, str):
            try:
                phishing_example_json = json.loads(phishing_example)

                phishing_email = PhishingEmail(**phishing_example_json)

                return phishing_email
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=500, detail=f"JSON parsing error: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Generated phishing example is empty or not a valid string.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")