import os

DB_USERNAME = os.environ['DB_USERNAME']
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']
DB_NAME = os.environ['DB_NAME']

ROOT_DIR = os.path.abspath(os.path.join('..'))
STATIC_DIR = os.path.abspath(os.path.join(
    ROOT_DIR, 'static'))
DATA_DIR = os.path.abspath(
    os.path.join(ROOT_DIR, 'static', 'data'))

#DB_CONNECTION_STRING = f"sqlite://{DATA_DIR}/{{filename}}.sqlite3"
DB_CONNECTION_STRING = F"postgres://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

MESSAGES_FILEPATH = os.path.join(STATIC_DIR, 'messages.out')

ALLOWED_UPLOAD_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
]