# fastapi_starter

> **DRAFT: initial assessment. TODO: to be finished after the rework.**

## What this seems to be

A personal FastAPI "starter" / playground from late 2021. The idea: a ready-to-clone
skeleton that already wires up the things a small FastAPI service usually needs, shown
on a toy **pizza** domain (pizzas, toppings, chefs):

- async REST CRUD on a database (Tortoise ORM; Postgres in compose, SQLite while playing)
- Pydantic request/response schemas
- background work: FastAPI `BackgroundTasks` *and* a Celery worker on Redis (+ Flower)
- file uploads (PDF / XLSX), Jinja2 templates, a WebSocket echo, static files
- an outgoing HTTP client (aiohttp singleton) calling an external API
- CORS so a separate React client (`client/`, Create React App + antd + Redux) can list pizzas
- Docker / docker-compose for the whole stack

Around it sit loose experiments: `src/db_example.py` (Tortoise query cookbook on a music
dataset), `src/helpers.py` (pandas/openpyxl poking at an Excel sample) and `examples/`
(OSM, folium, dash, bokeh visualisation snippets, unrelated to the API).

## Current state (honest assessment)

Works, in principle, only inside the compose stack:

- `src/config.py` reads `DB_*` env vars with `os.environ[...]` at import time, so nothing
  imports (not even tests) without a Postgres configured.
- Paths like `'../static'` and `'../templates'` only resolve when the cwd is `src/`.
- `Dockerfile` runs `apt update && apt upgrade` without `-y`, which aborts a non-interactive build.
- `docker-compose.yml` uses Celery 4 syntax (`celery worker --app=...`), Postgres 10.5,
  compose file `version: "2"`, a pgAdmin with placeholder credentials.
- Startup both calls `Tortoise.init` manually *and* `register_tortoise`, then re-seeds
  random toppings on every boot (silently swallowing `IntegrityError`).
- `POST /pizza/` ignores the chef, catches the wrong exception for duplicates
  (`OperationalError` instead of `IntegrityError`) and returns ad-hoc dicts.
- Upload endpoint writes `file.filename` straight into `static/` (path traversal) and
  answers unsupported types with `405` instead of `415`.
- WebSocket demo JS hardcodes `ws://localhost:8099`.
- Dependencies: FastAPI 0.70 / Pydantic 1 / Starlette 0.16 / Python 3.8; `Pipfile` +
  `Pipfile.lock` + `requirements.txt` side by side; many unused heavy deps (pandas, scipy,
  seaborn, matplotlib, xlwt, ...), and `jwt==1.3.1` which is not PyJWT.
- React client: CRA 4 (deprecated), React 17, an unused Redux store, the default
  `App.test.js` that fails ("learn react").
- Committed junk: `.idea/`, `static/data/pizza.sqlite3`, an 83 KB `Financial Sample.xlsx`.
- No tests, no lint config. No secrets found (only `postgres/postgres` defaults and a
  `myemail@gmail.com` placeholder in compose).

## TODO / to be finished

- [ ] Rebuild as a clean 2026 starter (FastAPI + Pydantic v2 + pydantic-settings,
      SQLAlchemy 2 async, Alembic, a current worker story, ruff, pytest)
- [ ] Decide on the React client (modernise with Vite)
- [ ] Usage docs, tests, cleanup of junk files
