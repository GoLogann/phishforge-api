from typing import List, Union
import torch
from sentence_transformers import SentenceTransformer


class SentenceTransformersEmbeddingClient:
    def __init__(self, model_name: str):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name).to(self.device)

    def embed(self, texts: Union[str, List[str]], normalize: bool = True):
        if isinstance(texts, str):
            texts = [texts.strip()]
            single_input = True
        else:
            texts = [t.strip() for t in texts]
            single_input = False

        embeddings = self.model.encode(
            texts,
            convert_to_tensor=True,
            normalize_embeddings=False
        ).to(self.device)

        if normalize:
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

        result = embeddings.cpu().numpy()
        return result[0].tolist() if single_input else result.tolist()
