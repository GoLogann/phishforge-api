from dependency_injector import containers, providers

from qdrant_client import QdrantClient

from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import settings
from app.domain.services.document_processor import DocumentProcessor
from app.domain.services.embedding_service import EmbeddingService
from app.domain.services.openai.embedding_client import OpenAIEmbeddingClient
from app.domain.services.phishing_service import PhishingEmailService
from app.domain.services.pipeline import IngestionPipeline
from app.domain.services.prompt_normalizer import PromptNormalizer
from app.domain.services.reranker import ReRanker
from app.domain.services.response_generator import ResponseGenerator
from app.domain.services.retriever import DocumentRetriever
from app.domain.services.sentence_transformers.embedding_client import SentenceTransformersEmbeddingClient
from app.infra.database.connection import DatabaseConnection
from app.infra.database.repositories.analytics_repository import AnalyticsRepository
from app.infra.database.repositories.phishing_repository import PhishingEmailRepository
from app.infra.qdrant.store import QdrantVectorStore

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["app.api.v1.endpoints"] 
    )

    config = providers.Configuration()
    config.from_dict(settings.dict())

    db_connection = providers.Singleton(
        DatabaseConnection,
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
    )

    qdrant_client = providers.Singleton(
        QdrantClient,
        url=config.QDRANT_URL,
    )

    embedding_client_st = providers.Singleton(
        SentenceTransformersEmbeddingClient,
        model_name=config.MODEL_NAME_EMBEDDING
    )

    embedding_client_openai = providers.Singleton(
        OpenAIEmbeddingClient,
        api_key=config.OPENAI_API_KEY,
        model="text-embedding-3-small"
    )

    qdrant_store = providers.Singleton(
        QdrantVectorStore,
        client=qdrant_client,
        embedding_client=embedding_client_openai,  # ou troca por embedding_client_st se quiser
    )
    
    reranker = providers.Factory(
        ReRanker
    )

    phishing_repository = providers.Factory(
        PhishingEmailRepository,
        db=db_connection
    )

    analytics_repository = providers.Factory(
        AnalyticsRepository,
        db=db_connection
    )


    embedding_service = providers.Factory(
        EmbeddingService,
        embedding_client=embedding_client_st  # ou embedding_client_openai
    )

    response_generator = providers.Factory(
        ResponseGenerator,
        api_key=config.OPENAI_API_KEY,
        model_name=config.MODEL_NAME_LLM,
    )
    
    prompt_normalizer = providers.Factory(
        PromptNormalizer,
        api_key=config.OPENAI_API_KEY
        # O model_name "gpt-4o-mini" será usado como default da própria classe
    )

    retriever = providers.Factory(
        DocumentRetriever,
        vector_store=qdrant_store
    )

    phishing_service = providers.Factory(
        PhishingEmailService,
        repository=phishing_repository,
        analytics_repository=analytics_repository
    )

    pipeline = providers.Factory(
        IngestionPipeline,
        processor=providers.Factory(DocumentProcessor),
        vector_store=qdrant_store
    )
    
    chat_openai_model = providers.Factory(
        ChatOpenAI,
        model="gpt-4o-mini", 
        api_key=config.OPENAI_API_KEY
    )

    openai_embeddings_model = providers.Factory(
        OpenAIEmbeddings,
        model="text-embedding-3-large", 
        api_key=config.OPENAI_API_KEY
    )
    
    evaluation_llm = providers.Singleton(
        LangchainLLMWrapper,
        langchain_llm=chat_openai_model,
    )

    evaluation_embeddings = providers.Singleton(
        LangchainEmbeddingsWrapper,
        embeddings=openai_embeddings_model 
    )