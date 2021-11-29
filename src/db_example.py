import json
import os

from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import date, datetime as dt, timedelta as td
from enum import Enum, auto
from typing import Type

from tortoise import (Tortoise, ConfigurationError,
    fields, run_async)
from tortoise.exceptions import OperationalError
from tortoise.fields import CharField
from tortoise.functions import Length
from tortoise.models import Model
from tortoise.transactions import atomic, in_transaction

from config import DATA_DIR, DB_CONNECTION_STRING

class Gender(Enum):
    MALE = auto()
    FEMALE = auto()
    @classmethod
    def find_value(cls, value):
        for constant in list(cls):
            if constant.name.lower() == value:
                return constant
        raise ValueError(f"Cannot find constant associated with {value}")

class EnumField(CharField):
    def __init__(self, enum_type: Type[Enum], **kwargs):
        super().__init__(128, **kwargs)
        if not issubclass(enum_type, Enum):
            raise ConfigurationError(f"{enum_type} is not a subclass of Enum!")
        self._enum_type = enum_type

    def to_db_value(self, value: Enum, instance) -> str:
        return value.value

    def to_python_value(self, value: int) -> Enum:
        try:
            if isinstance(value, self._enum_type):
                return value
            elif isinstance(value, str) and value.isdigit():
                return self._enum_type(int(value))
        except Exception:
            raise ValueError(f"Database value {value} doesn not exist on Enum {self._enum_type}.")

class Ordinal(Enum):
    ST, ND, RD, TH = range(1, 5)
    @classmethod
    def check(cls, num):
        num %= 10

        items = { i.value: i.name.lower() for i in list(cls) }

        if num not in list(items.keys())[:-1]:
            return items[4]
        else:
            return items[num]

@dataclass(frozen = True)
class ArtistIn:
    name: str
    gender: Gender

@dataclass(frozen = True)
class AlbumIn:
    title: str
    release_date: date

def load_data():
    data = defaultdict(list)

    with open(os.path.join(DATA_DIR, 'records.json')) as f:
        doc = json.loads(f.read())

        for artist in doc['artists']:
            artist_in = ArtistIn(name = artist['name'],
                gender = Gender.find_value(artist['singer_gender']))

            for album in artist['albums']:
                album_in = AlbumIn(**album)
                data[artist_in].append(album_in)

    return data

class Artist(Model):
    id = fields.IntField(pk = True)
    name = fields.TextField()
    singer_gender = EnumField(Gender)

class Album(Model):
    id = fields.IntField(pk = True)
    title = fields.TextField()
    release_date = fields.DateField()
    artist = fields.ForeignKeyField('models.Artist')

async def populate(data):
    for artist, albums in data.items():
        artist = await Artist.create(name = artist.name,
           singer_gender = artist.gender)

        for album in albums:
            album = Album(**asdict(album), artist = artist)
            await album.save()

async def create_dummy():
    artist = await Artist.create(name = 'Pop King',
        singer_gender = Gender.MALE)

    album = Album(title = 'Your next best song',
        release_date = dt.now(), artist = artist)

    album.release_date += td(days = 1)

    await album.save()

async def run_queries():
    record = await Artist.filter(name__contains = 'Q').first()
    print('First record starting with Q:', record.name)

    async for album in Album.all().prefetch_related('artist'):
        date_string = album.release_date\
            .strftime('%B %-d{ordinal} %Y'\
            .format(ordinal = Ordinal.check(album.release_date.day)))

        msg = f"{album.title} by {album.artist.name} released on {date_string}"
        print(msg)

    print(await Album.filter(title__icontains = 'at').values('title'))

    for artist in await Artist.all().group_by('-singer_gender'):
        print(artist.name, 'is', artist.singer_gender.name.lower())

    print(await Artist.filter(name__startswith = 'P').get_or_none(id = 1))

    print(await Album.filter(artist = record).count())

    print(Album.filter(release_date__gt = date(2000, 1, 1)).sql())

    print((await Album.annotate(length = Length('title')).order_by('-length').first()).length)

    print(await Album.all().offset(3).limit(2))

    print(await Artist.filter(name__in = {'Queen', 'Panic! At The Disco'}))

    print(await Artist.filter(name__iexact = 'panic! at the disco'))

    conn = Tortoise.get_connection('default')
    query = 'SELECT name FROM Artist'
    result = await conn.execute_query(query)
    for row in result[1]:
        print(row['name'])

    try:
        async with in_transaction() as connection:
            album = Album(title = 'Kind of Magic', release_date = date(1986, 6, 2),
                artist = artist)
            await album.save(using_db = connection)

            await Album.filter(id = album.id).using_db(connection).update(title = 'A Kind of Magic')

            saved_album = await Album.filter(title = "A Kind of Magic").using_db(connection).first()

            await connection.execute_query("SELECT * FROM non_existent_table")

            print(saved_album.title)
    except OperationalError as e:
        print(f'There was an error: \'{e}\'. Reverting.')
        pass

    albums = {d['title'] for d in await Album.all().values('title')}
    print(albums)

    print(set(await Artist.all().values_list('singer_gender')))

    for obj in await Album.filter(release_date__range = (date(1970, 1, 1), date(1980, 1, 1))):
        print(obj.release_date)

    print(await record.albums.all())

async def init():
    await Tortoise.init(
        db_url = DB_CONNECTION_STRING,
        modules = { 'models': [__name__] }
    )
    await Tortoise.generate_schemas()

    await Artist.all().delete()
    await Album.all().delete()

    await populate(load_data())
    await create_dummy()

    await run_queries()

    await Tortoise.close_connections()

if __name__ == '__main__':
    run_async(init())
