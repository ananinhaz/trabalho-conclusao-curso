from ..repositories import animal_repo as repo
from ..schemas.animal_schema import AnimalIn

def listar(limit=50):
    return repo.list_all(limit)

def obter(aid: int):
    return repo.get_by_id(aid)

def criar(data: dict):
    payload = AnimalIn(**data).model_dump()
    new_id = repo.insert(payload)
    return {"id": new_id, **payload}

def atualizar(aid: int, data: dict):
    payload = AnimalIn(**data).model_dump()
    ok = repo.update(aid, payload)
    return ok > 0

def remover(aid: int):
    return repo.delete(aid) > 0
