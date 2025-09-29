from typing import Dict
from pydantic import BaseModel, Field


class EmailStatistics(BaseModel):
    total: int = Field(default=0, ge=0)
    by_difficulty: Dict[str, int] = Field(default_factory=lambda: {"facil": 0, "medio": 0, "dificil": 0})
    by_category: Dict[str, int] = Field(default_factory=dict)
    recent_count: int = Field(default=0, ge=0)