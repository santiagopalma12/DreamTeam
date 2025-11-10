# modelos ligeros/DTOs si se necesitan
from pydantic import BaseModel
from typing import List


class Empleado(BaseModel):
    id: str
    nombre: str
    zona: str = None
    rol: str = None
    acceso: List[str] = []