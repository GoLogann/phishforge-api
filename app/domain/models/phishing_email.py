from pydantic import BaseModel
from typing import List

class PhishingEmail(BaseModel):
    receptor: str
    remetente: str
    assunto: str
    conteudo: str
    explicacao: str
    nivel: str
    categoria: str
    links: List[str]