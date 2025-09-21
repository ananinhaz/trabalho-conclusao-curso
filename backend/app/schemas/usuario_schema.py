from pydantic import BaseModel, EmailStr, Field

class UsuarioIn(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    email: EmailStr

class UsuarioOut(UsuarioIn):
    id: int
