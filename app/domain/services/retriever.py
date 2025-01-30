from app.infrastructure.qdrant.store import QdrantVectorStore


class DocumentRetriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store
    @staticmethod
    def retrieve_relevant_documents(collection_name, query_embedding):
        qdrant = QdrantVectorStore()

        search_result = qdrant.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=10
        )

        return " ".join([hit.payload['text'] for hit in search_result])
