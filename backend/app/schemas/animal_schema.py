from pydantic import BaseModel, Field

class AnimalIn(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    especie: str = Field(min_length=1, max_length=60)
    idade: int = Field(ge=0)

class AnimalOut(AnimalIn):
    id: int
