from typing import Optional

from pydantic import BaseModel

class QueryRequest(BaseModel):
    difficulty: Optional[int]
    context: Optional[str]

    class Config:
        populate_by_name = True
        from_attributes = True

class QueryResponse(BaseModel):
    text: str

class RepoRequest(BaseModel):
    url: str