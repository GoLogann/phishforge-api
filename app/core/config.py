from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MODEL_NAME_EMBEDDING: str = "all-MiniLM-L6-v2"
    MODEL_NAME_LLM: str = "deepseek-r1:7b"
    QDRANT_URL: str = "http://localhost:6333"
    CHUNK_SIZE: int = 350
    CHUNK_OVERLAP: int = 20
    TOP_K_DOCUMENTS: int = 4

settings = Settings()