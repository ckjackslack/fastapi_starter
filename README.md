# fastapi_starter

A small, current (2026) FastAPI project template. Clone it, rename the pizza domain to
your own, and you already have the boring parts wired up and tested:

| Concern | What's in the box |
| --- | --- |
| API | FastAPI 0.16x, Pydantic v2 schemas, domain errors mapped to proper status codes |
| Config | `pydantic-settings`: `APP_*` env vars or `.env`, sane defaults, no env needed to start |
| Database | SQLAlchemy 2 async (SQLite by default, Postgres via `asyncpg`), Alembic migrations |
| Background work | FastAPI `BackgroundTasks` for fire-and-forget, **Taskiq** jobs with pollable results |
| Files | streamed uploads with type/size limits and safe names, download, `.xlsx` preview |
| Outgoing HTTP | one shared `httpx2.AsyncClient`, injected so tests mock it |
| Web bits | Jinja2 page, static files, WebSocket echo, CORS for the dev front-end |
| Front-end | `client/`: React 19 + Vite 8 app using the API |
| Ops | `fastapi-starter` CLI, uv-based Dockerfile, compose stack (API, worker, Postgres, Redis) |
| Quality | ruff (lint + format), pytest suite that needs no Redis/Postgres/Docker/network |

The demo domain is the one from the original prototype: **pizzas** with an optional **chef**
and many **toppings**.

## Quick start

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'          # or: uv sync --extra dev
cp .env.example .env             # optional, defaults work as they are

fastapi-starter migrate          # create data/app.db via Alembic
fastapi-starter seed             # demo chefs, toppings, pizzas (idempotent)
fastapi-starter serve --reload   # http://127.0.0.1:8000  (docs at /docs)
```

`fastapi-starter serve --migrate --seed` does all three in one go. Plain uvicorn works too:
`uvicorn fastapi_starter.main:app` (or `--factory fastapi_starter.main:create_app`).

## Using the API

These were run against a freshly seeded database:

```console
$ curl -s 'localhost:8000/api/pizzas?topping=basil'
{"items":[{"id":1,"name":"Margherita","chef":{"id":1,"name":"Mario"},
  "toppings":[{"id":6,"name":"Basil"},{"id":4,"name":"Mozzarella"},{"id":5,"name":"Tomato sauce"}],
  "created_at":"2026-10-22T19:46:58.812397Z"}],"total":1,"limit":50,"offset":0}

$ curl -s -X POST localhost:8000/api/pizzas -H 'content-type: application/json' \
    -d '{"name": "diavola", "chef_id": 1, "toppings": ["tomato sauce", "mozzarella", "pepperoni"]}'
{"id":4,"name":"Diavola","chef":{"id":1,"name":"Mario"},"toppings":[{"id":4,"name":"Mozzarella"},
  {"id":1,"name":"Pepperoni"},{"id":5,"name":"Tomato sauce"}],"created_at":"2026-10-22T19:47:00.376122Z"}

$ curl -s -X POST localhost:8000/api/pizzas/4/bake -H 'content-type: application/json' -d '{"seconds": 0}'
{"task_id":"9de1022a508245d1a181e895afe1fad7"}
$ curl -s localhost:8000/api/tasks/9de1022a508245d1a181e895afe1fad7
{"task_id":"9de1022a508245d1a181e895afe1fad7","status":"success",
  "result":"Diavola is ready after 0s in the oven.","error":null}

$ curl -s -F 'file=@sales.xlsx;type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' \
    localhost:8000/api/files
{"name":"sales.xlsx","size":4970,"content_type":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
$ curl -s 'localhost:8000/api/files/sales.xlsx/preview?rows=2'
{"sheet":"Sales","header":["Country","Product","Units"],
  "rows":[["Canada","Carretera",1618],["Germany","Paseo",1321]],"total_rows":4,"total_columns":3}

$ curl -s -F 'file=@sales.xlsx;type=image/png' localhost:8000/api/files     # -> 415
{"detail":"Content type 'image/png' is not allowed. Allowed: application/pdf, ..."}
```

Endpoints (`fastapi-starter routes` prints this list):

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/pizzas` | `limit`, `offset`, `topping`, `chef`, `q` filters; `X-Total-Count` header |
| POST | `/api/pizzas` | `{name, chef_id?, toppings: [names]}`; 409 duplicate, 422 unknown topping/chef |
| GET / PATCH / DELETE | `/api/pizzas/{id}` | PATCH changes only the fields you send |
| POST | `/api/pizzas/{id}/bake` | queue a Taskiq job, `{seconds}` (0-60), returns `task_id` |
| GET | `/api/tasks/{task_id}` | `pending` / `success` / `failure` with result or error |
| POST / GET | `/api/tasks/messages` | `BackgroundTasks` demo: appends to / tails `APP_MESSAGE_LOG` |
| GET / POST | `/api/chefs`, `/api/toppings` | names are normalised (`" tomato  sauce"` becomes `"Tomato sauce"`) |
| POST / GET | `/api/files` | upload (PDF/CSV/XLSX by default, size-limited), list |
| GET | `/api/files/{name}`, `/api/files/{name}/preview` | download, spreadsheet preview (`rows`, `sheet`) |
| GET | `/api/external/todos/{id}` | proxied JSONPlaceholder call; upstream failures become 502 |
| GET | `/api/healthz` | version + database ping, 503 when the DB is unreachable |
| GET | `/` | Jinja2 page listing pizzas, with a WebSocket chat box |
| WS | `/ws/echo` | echoes text back |

## Configuration

All settings are `APP_`-prefixed environment variables (or lines in `.env`, see
`.env.example`). Lists accept `a,b,c` or a JSON array.

| Variable | Default | Meaning |
| --- | --- | --- |
| `APP_DATABASE_URL` | `sqlite+aiosqlite:///./data/app.db` | any async SQLAlchemy URL |
| `APP_BROKER_URL` | *(empty)* | empty: jobs run in-process; `redis://...`: external worker |
| `APP_CORS_ORIGINS` | `http://localhost:5173` | allowed browser origins |
| `APP_UPLOAD_DIR` | `data/uploads` | where uploads are stored |
| `APP_MAX_UPLOAD_BYTES` | `10485760` | per-file limit (413 above it) |
| `APP_ALLOWED_UPLOAD_TYPES` | PDF, CSV, XLSX | allowed content types (415 otherwise) |
| `APP_MESSAGE_LOG` | `data/messages.log` | file written by the `BackgroundTasks` demo |
| `APP_EXTERNAL_API_URL` | `https://jsonplaceholder.typicode.com` | upstream for `/api/external` |
| `APP_EXTERNAL_API_TIMEOUT` | `5.0` | seconds |
| `APP_ENVIRONMENT`, `APP_DEBUG`, `APP_LOG_LEVEL`, `APP_DATABASE_ECHO` | `dev`, `false`, `INFO`, `false` | |

## Background work

Two flavours, on purpose:

* **`BackgroundTasks`** (`POST /api/tasks/messages`): runs after the response in the same
  process. Fine for tiny fire-and-forget jobs; no result, no retries.
* **Taskiq** (`POST /api/pizzas/{id}/bake` then `GET /api/tasks/{id}`): an async-native task
  queue. With `APP_BROKER_URL` empty it uses Taskiq's `InMemoryBroker`, so jobs run inside the
  web process: zero infrastructure for development and tests. Set
  `APP_BROKER_URL=redis://localhost:6379/0`, install the `redis` extra and start
  `fastapi-starter worker` (a wrapper around `taskiq worker fastapi_starter.worker:broker`)
  and the same code runs on a separate worker via a Redis stream, results in Redis.

Add your own jobs in `src/fastapi_starter/worker.py` with `@broker.task`.

## Database and migrations

Models live in `models.py` (SQLAlchemy 2 typed `Mapped[...]` style, a naming convention for
constraints, UTC-aware timestamps on every backend). Migrations live inside the package so
`fastapi-starter migrate` works from an installed wheel / Docker image.

```sh
# after changing models.py
alembic revision --autogenerate -m "add crust to pizza"   # uses alembic.ini + APP_DATABASE_URL
fastapi-starter migrate
```

`alembic check` (and `tests/test_cli_and_migrations.py`) fail if models and migrations drift.
SQLite migrations run in Alembic batch mode, so `ALTER`-style changes work there too.

## CLI

```console
$ fastapi-starter --help
usage: fastapi-starter [-h] [--version] COMMAND ...
    serve     run the web app with uvicorn          (--host --port --reload --migrate --seed)
    migrate   apply Alembic migrations              (optional revision, default head)
    seed      insert demo chefs, toppings and pizzas (idempotent)
    routes    list all HTTP/WebSocket routes
    worker    run the Taskiq worker (needs a redis:// broker)
```

Bad configuration (e.g. `APP_MAX_UPLOAD_BYTES=lots`) exits with code 2 and a readable message.

## React client

`client/` is a small Vite + React 19 app (list, create, delete, bake with live status). Its
dev server proxies `/api` to the backend, so there is no CORS dance during development:

```sh
cd client && npm install && npm run dev    # http://localhost:5173
```

## Docker

```sh
docker compose up --build                  # api :8000, worker, postgres 18, redis 8
docker compose exec api fastapi-starter seed
```

The image is built with uv from `uv.lock`, runs as a non-root user, applies migrations on
start and has a healthcheck on `/api/healthz`. Install extras locally with
`pip install -e '.[prod]'` (`asyncpg` + `taskiq-redis`).

## Project layout

```
src/fastapi_starter/
  main.py          app factory (lifespan: engine, httpx2 client, broker), error handler
  config.py        Settings (pydantic-settings)
  db.py            async engine/session, Base, UTCDateTime, ping
  models.py        Chef, Topping, Pizza (+ pizza_topping)
  schemas.py       Pydantic models, name normalisation
  crud.py          database operations, raise domain errors (errors.py)
  worker.py        Taskiq broker factory + bake_pizza job
  middleware.py    X-Request-ID / X-Process-Time
  seed.py          deterministic demo data
  cli.py           fastapi-starter command
  api/             routers: pizzas, tasks, files, misc (health, external), pages (HTML, WS)
  services/        storage (uploads), spreadsheet (xlsx preview), external (HTTP)
  migrations/      Alembic env + versions
  templates/, static/
client/            React + Vite front-end
tests/             pytest suite
```

## Design notes: what changed from the 2021 prototype

The original was a playground: Tortoise ORM experiments, a Celery worker, an aiohttp
singleton, a CRA client, Excel and plotting snippets. It only ran inside its compose stack
(config read `DB_*` env vars at import time, paths were relative to `src/`). The rework keeps
its spirit, a starter showing the usual pieces of a FastAPI service on a pizza demo, and
rebuilds it:

| Was | Now | Why |
| --- | --- | --- |
| Python 3.8, FastAPI 0.70, Pydantic 1, Starlette 0.16 | Python >= 3.12, FastAPI 0.161, Pydantic 2.14, Starlette 1.9 | current stack |
| `os.environ[...]` constants | `pydantic-settings` with defaults | starts (and tests) with zero env |
| Tortoise ORM + `generate_schemas` + random reseed on every boot | SQLAlchemy 2 async + Alembic + idempotent `seed` | mainstream ORM, real migrations |
| Celery 4 + Flower, `celery worker` syntax | Taskiq (in-memory or Redis streams) | async-native, no infra needed in dev/tests |
| aiohttp `ClientSession` singleton | `httpx2.AsyncClient` owned by the lifespan | injectable and mockable; httpx2 is what Starlette 1.x expects |
| `@app.on_event` | lifespan context manager | `on_event` is deprecated |
| Pipfile + Pipfile.lock + requirements.txt | `pyproject.toml` (PEP 621, hatchling) + `uv.lock` | one source of truth |
| CRA 4 + React 17 + Redux + antd | Vite 8 + React 19, plain fetch | CRA is dead; the Redux store was unused |
| `docker-compose.yml` v2, Postgres 10, pgAdmin, `apt upgrade` without `-y` | `compose.yaml`, Postgres 18, Redis 8, healthchecks, uv multi-stage image | the old build could not run unattended |
| no tests, no linter | pytest (71 tests) + ruff | |

Bugs fixed along the way: uploads wrote `file.filename` verbatim (path traversal), wrong
status codes (405 for a bad type, now 415; ad-hoc dicts, now `HTTPException`-style JSON),
`POST /pizza` ignored the chef and caught the wrong exception for duplicates, the
WebSocket JS hardcoded `ws://localhost:8099`.

Removed: `.idea/`, the committed `pizza.sqlite3` and 83 KB `Financial Sample.xlsx`,
`src/db_example.py` (a Tortoise query cookbook on a music dataset) and `examples/` (OSM,
folium, dash and bokeh snippets that had nothing to do with the API and needed the internet).
They remain in git history.

### Goodies

* **Pagination and filters** on `GET /api/pizzas` (`limit`/`offset`, by topping, chef, name
  substring) with a `Page` response and `X-Total-Count` header.
* **`/api/healthz`** with a real database ping: 200 when fine, 503 when the DB is down; used
  by the Docker healthcheck.
* **Request ID and timing middleware**: every response gets `X-Request-ID` (an incoming one
  from a proxy is reused if it looks sane) and `X-Process-Time`, and it is logged.
* **Spreadsheet preview** for uploaded `.xlsx` files (header, first N rows, totals; choose
  the sheet), the useful core of the old `helpers.py` pandas/openpyxl experiment.
* **`fastapi-starter` CLI** with `serve`, `migrate`, `seed`, `routes` and `worker`.

## Tests

```sh
pytest            # 71 tests, ~4 s
ruff check . && ruff format --check .
```

Every test uses a temporary SQLite file, the in-memory Taskiq broker and an
`httpx2.MockTransport` upstream; nothing touches Redis, Postgres, Docker or the network.
Covered: name normalisation, schemas, settings parsing, broker selection, filename
sanitising, spreadsheet preview, all CRUD paths and error codes, both background-work
flavours, uploads (traversal, 413, 415), health, external errors, middleware headers, CORS,
the HTML page, WebSocket, the CLI commands, and Alembic upgrade/downgrade plus a
"models match migrations" check. One test runs the app through `httpx2.AsyncClient` +
`ASGITransport` in the test's own event loop.

## Known limitations

* The Docker image and compose stack (Postgres + Redis + separate Taskiq worker) were
  written for current images but **not run here** (no Docker daemon available); the uv
  install path they use was verified locally. The Redis broker is only checked to construct.
* `/api/external/...` was only tested against a mocked upstream (no internet in the build
  environment).
* The React client was built (`npm run build`) and its dev proxy checked with curl, not
  clicked through in a browser.
* Task status cannot tell "unknown id" from "queued": both report `pending`. With the
  in-memory broker results live in process memory (last 100) and vanish on restart.
* No authentication. The original README listed "OAuth2 + JWT (todo)" but never started
  it; add it on top (e.g. FastAPI's `OAuth2PasswordBearer` + PyJWT) when you need it.
