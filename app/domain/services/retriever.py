class DocumentRetriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def retrieve_relevant_documents(self, collection_name: str, query_embedding):
        search_result = self.vector_store.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=10
        )
        return " ".join([hit.payload['text'] for hit in search_result])
