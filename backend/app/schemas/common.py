from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    ok: bool


class AuthUser(BaseModel):
    id: int
    display_name: str
    is_demo: bool
    image_url: str | None = None


class TransitionEdge(BaseModel):
    source: str
    target: str
    count: int
    probability: float = Field(ge=0, le=1)
