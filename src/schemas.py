from pydantic import BaseModel, Field
from typing import List
from itertools import count

ID_GEN = count(start = 1)

class PizzaIn(BaseModel):
    name: str
    toppings: List[str]

class Pizza(BaseModel):
    name: str
    toppings: List[str]
    id: int = Field(default_factory = lambda: next(ID_GEN))