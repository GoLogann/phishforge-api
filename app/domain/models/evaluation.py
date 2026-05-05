from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EvaluationSession(BaseModel):
    """Model para sessões de avaliação RAGAS."""
    
    id: Optional[UUID] = None
    session_name: Optional[str] = None
    description: Optional[str] = None
    status: str = Field(default="pending", pattern="^(pending|running|completed|failed)$")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_evaluations: int = Field(default=0, ge=0)
    successful_evaluations: int = Field(default=0, ge=0)
    failed_evaluations: int = Field(default=0, ge=0)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RagasEvaluation(BaseModel):
    """Model para avaliações RAGAS individuais."""
    
    id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    email_id: UUID
    user_context: str
    search_query: str
    generation_context: str
    difficulty: str
    hyde_context: Optional[str] = None
    fused_context: Optional[str] = None
    expanded_answer_pt: Optional[str] = None
    full_answer_pt: Optional[str] = None
    expanded_answer_en: Optional[str] = None
    full_answer_en: Optional[str] = None
    status: str = Field(default="pending", pattern="^(pending|running|completed|failed)$")
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EvaluationRetrievedDocument(BaseModel):
    """Model para documentos recuperados durante a avaliação."""
    
    id: Optional[UUID] = None
    evaluation_id: UUID
    document_order: int = Field(ge=0)
    document_id: Optional[str] = None
    document_text: str
    parent_content: Optional[str] = None
    similarity_score: Optional[Decimal] = Field(None, ge=0, le=1)
    rerank_score: Optional[Decimal] = Field(None, ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RagasMetric(BaseModel):
    """Model para métricas individuais do RAGAS."""
    
    id: Optional[UUID] = None
    evaluation_id: UUID
    metric_name: str = Field(max_length=50)
    metric_value: Optional[Decimal] = Field(None, ge=0, le=1)
    metric_category: Optional[str] = Field(None, max_length=30)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EvaluationSessionResult(BaseModel):
    """Model para resultados agregados por sessão."""
    
    id: Optional[UUID] = None
    session_id: UUID
    metric_name: str = Field(max_length=50)
    avg_value: Optional[Decimal] = Field(None, ge=0, le=1)
    min_value: Optional[Decimal] = Field(None, ge=0, le=1)
    max_value: Optional[Decimal] = Field(None, ge=0, le=1)
    std_deviation: Optional[Decimal] = Field(None, ge=0)
    median_value: Optional[Decimal] = Field(None, ge=0, le=1)
    total_samples: int = Field(ge=0)
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EvaluationMetricsSummary(BaseModel):
    """Model para view de resumo de métricas."""
    
    evaluation_id: UUID
    email_id: UUID
    difficulty: str
    status: str
    created_at: datetime
    metric_name: Optional[str] = None
    metric_value: Optional[Decimal] = None
    metric_category: Optional[str] = None

    class Config:
        from_attributes = True


class SessionPerformanceOverview(BaseModel):
    """Model para view de overview de performance da sessão."""
    
    session_id: UUID
    session_name: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_evaluations: int
    successful_evaluations: int
    failed_evaluations: int
    success_rate_percent: Optional[Decimal] = None
    duration_seconds: Optional[float] = None

    class Config:
        from_attributes = True


# DTOs para requisições e respostas da API

class CreateEvaluationSessionRequest(BaseModel):
    """DTO para criar uma nova sessão de avaliação."""
    
    session_name: Optional[str] = None
    description: Optional[str] = None


class CreateRagasEvaluationRequest(BaseModel):
    """DTO para criar uma nova avaliação RAGAS."""
    
    session_id: Optional[UUID] = None
    email_id: UUID
    user_context: str
    search_query: str
    generation_context: str
    difficulty: str
    hyde_context: Optional[str] = None
    fused_context: Optional[str] = None


class EvaluationProgress(BaseModel):
    """DTO para progresso de avaliação."""
    
    evaluation_id: UUID
    status: str
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    current_step: Optional[str] = None
    estimated_completion: Optional[datetime] = None


class MetricsSummaryResponse(BaseModel):
    """DTO para resposta de resumo de métricas."""
    
    session_id: Optional[UUID] = None
    evaluation_id: Optional[UUID] = None
    metrics: List[RagasMetric]
    avg_faithfulness: Optional[Decimal] = None
    avg_answer_relevancy: Optional[Decimal] = None
    avg_context_precision: Optional[Decimal] = None
    avg_context_recall: Optional[Decimal] = None
    total_evaluations: int


class EvaluationBatchRequest(BaseModel):
    """DTO para avaliação em lote."""
    
    session_name: Optional[str] = None
    evaluation_requests: List[CreateRagasEvaluationRequest]
    parallel_workers: int = Field(default=1, ge=1, le=10)


class EvaluationBatchResponse(BaseModel):
    """DTO para resposta de avaliação em lote."""
    
    session_id: UUID
    total_requested: int
    total_started: int
    estimated_completion_time: Optional[datetime] = None
    batch_status: str = Field(pattern="^(submitted|running|completed|failed)$")