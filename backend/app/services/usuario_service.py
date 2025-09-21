from ..repositories import usuario_repo as repo
from ..schemas.usuario_schema import UsuarioIn

def listar(limit=50):
    return repo.list_all(limit)

def obter(uid: int):
    return repo.get_by_id(uid)

def criar(data: dict):
    payload = UsuarioIn(**data).model_dump()
    new_id = repo.insert(payload)
    return {"id": new_id, **payload}

def atualizar(uid: int, data: dict):
    payload = UsuarioIn(**data).model_dump()
    ok = repo.update(uid, payload)
    return ok > 0

def remover(uid: int):
    return repo.delete(uid) > 0
