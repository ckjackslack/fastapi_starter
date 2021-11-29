import os

ROOT_DIR = os.path.abspath(os.path.join('..'))
DATA_DIR = os.path.abspath(
    os.path.join(ROOT_DIR, 'static', 'data'))

DB_CONNECTION_STRING = f"sqlite://{DATA_DIR}/music.sqlite3"