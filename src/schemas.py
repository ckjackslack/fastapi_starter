from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise import Tortoise
from pydantic import BaseModel
from models import Pizza
from pprint import pprint

class Topping_Pydantic(BaseModel):
    name: str

Tortoise.init_models(['models'], 'models')
Pizza_Pydantic = pydantic_model_creator(Pizza, name = 'Pizza')
PizzaIn_Pydantic = pydantic_model_creator(Pizza,
    name = 'PizzaIn', exclude_readonly = True)

# pprint(Pizza_Pydantic.schema())