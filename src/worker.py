import os
from celery import Celery

app = Celery(__name__, include = ['tasks'])
app.conf.broker_url = os.environ.get('CELERY_BROKER_URL')
app.conf.result_backend = os.environ.get('CELERY_RESULT_BACKEND')
