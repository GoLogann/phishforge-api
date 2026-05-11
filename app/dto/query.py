from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    difficulty: str
    user_context: str = Field(alias="context")

    class Config:
        populate_by_name = True
        from_attributes = True

class QueryResponse(BaseModel):
    text: str
    score: float | None = None
    id: str | None = None
    payload: dict | None = None # type: ignore

class RepoRequest(BaseModel):
    url: str