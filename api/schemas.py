from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str

class TextRequest(BaseModel):
    text: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AnalysisResult(BaseModel):
    score: float
    feedback: list[str]
    improved_text: str