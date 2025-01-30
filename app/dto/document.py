from typing import List

from pydantic import BaseModel


class Document(BaseModel):
    text: str
    embedding: List[float]