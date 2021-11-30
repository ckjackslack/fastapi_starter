from random import sample, randint

from tortoise import Tortoise, fields, models, run_async
from tortoise.utils import get_schema_sql
from tortoise.exceptions import IntegrityError

def debug():
    print(get_schema_sql(Tortoise.get_connection('default'), True))

class Topping(models.Model):
    id = fields.IntField(pk = True)
    name = fields.CharField(max_length = 128, unique = True)

class Pizza(models.Model):
    id = fields.IntField(pk = True)
    name = fields.CharField(max_length = 128, unique = True)
    toppings = fields.ManyToManyField('models.Topping')
    chef = fields.ForeignKeyField('models.Chef', related_name = 'chef',
        on_delete = fields.SET_NULL, null = True)

class Chef(models.Model):
    id = fields.IntField(pk = True)
    name = fields.CharField(max_length = 128, unique = True)

async def populate_db():
    try:
        chefs = ['Mario', 'Luigi', 'Gordon Ramsey']
        for chef in chefs:
            await Chef.create(name = chef)

        toppings = ['Pepperoni', 'Ham', 'Pineapple',
            'Mozzarella', 'Tomato sauce']
        for topping in toppings:
            db_obj = Topping(name = topping)
            await db_obj.save()

        chefs = await Chef.all()
        toppings = await Topping.all()

        pizzas = ['Italian', 'Hawaiian', 'French']
        for chef, pizza in zip(chefs, pizzas):
            db_obj = Pizza(name = pizza, chef = chef)
            await db_obj.save()

            for topping in sample(toppings, k = randint(1, 3)):
                await db_obj.toppings.add(topping)
    except IntegrityError:
        pass

async def check_queries():
    print('Available toppings:')
    async for t in Topping.all().values_list():
        print(t)

    async for p in Pizza.all().prefetch_related('toppings', 'chef'):
        for topping in await p.toppings.all():
            print(p.name, 'has', topping.name, 'made by', p.chef.name)

    some_pizza = await Pizza.get_or_none(id = 1)
    if some_pizza:
        print(some_pizza.name, 'is losing chef')
        some_pizza.chef = None
        await some_pizza.save()

    for pizza in await Pizza.filter(chef_id__not_isnull = True):
        print(pizza.name, 'still has chef')
        pizza.name += '!'
        await pizza.save()

    async for pizza in Pizza.all():
        print(pizza.name)

async def create_and_populate_db():
    await Tortoise.init(
        db_url = 'sqlite://:memory:',
        modules = {'models': ['__main__']}
    )

    await Tortoise.generate_schemas()
    debug()

    await populate_db()
    await check_queries()

if __name__ == '__main__':
    run_async(create_and_populate_db())