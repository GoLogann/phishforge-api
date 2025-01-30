from app.core.config import settings
from sentence_transformers import SentenceTransformer
import torch

class SentenceTransformersEmbeddingClient:
    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(settings.MODEL_NAME_EMBEDDING).to(device)
        self.device = device

    def embed(self, text):
        embedding = self.model.encode(text, convert_to_tensor=True).to(self.device)
        return embedding.cpu().numpy().tolist()
