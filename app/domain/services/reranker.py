from typing import List
from sentence_transformers import CrossEncoder
from app.dto.query import QueryResponse 

class ReRanker:
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: List[QueryResponse]) -> List[QueryResponse]:
        if not documents:
            return []
            
        # O cross-encoder precisa de pares [query, document_text]
        pairs = [[query, doc.text] for doc in documents]
        
        # Calcula as pontuações de relevância
        scores = self.model.predict(pairs)
        
        # Adiciona as novas pontuações aos documentos
        for doc, score in zip(documents, scores):
            doc.score = float(score) # Atualiza o score com o do re-ranker
            
        # Reordena os documentos pela nova pontuação, do maior para o menor
        sorted_docs = sorted(documents, key=lambda x: x.score, reverse=True)
        
        return sorted_docs