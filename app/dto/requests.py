from typing import List

from pydantic import BaseModel, Field


class BatchGenerationRequest(BaseModel):
    """Request DTO para geração em lote de emails de phishing"""
    context: str = Field(description="Contexto para geração dos emails")
    difficulties: List[str] = Field(description="Lista de dificuldades desejadas")
    total: int = Field(default=10, ge=1, le=10, description="Total de emails a serem gerados")


class EmailSearchRequest(BaseModel):
    """Request DTO para busca de emails"""
    categoria: str | None = Field(None, description="Filtrar por categoria")
    nivel: str | None = Field(None, description="Filtrar por nível de dificuldade")
    search: str | None = Field(None, description="Termo de busca")
    limit: int = Field(default=50, ge=1, le=100, description="Limite de resultados")
    offset: int = Field(default=0, ge=0, description="Offset para paginação")


class UserAnswerEvaluationRequest(BaseModel):
    """Request DTO para avaliação da justificativa do usuário"""
    phishing_example: str = Field(
        description="O exemplo de phishing que foi apresentado ao usuário"
    )
    user_justification: str = Field(
        description="A justificativa do usuário explicando por que o exemplo é phishing"
    )