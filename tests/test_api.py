"""HTTP-level tests through the real app (lifespan included), SQLite + in-memory broker."""

from __future__ import annotations

import time
from pathlib import Path

import httpx2
import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from fastapi_starter.config import Settings
from fastapi_starter.main import create_app

PDF = "application/pdf"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# --- pizzas -------------------------------------------------------------------------------


def test_pizza_crud_roundtrip(seeded: TestClient) -> None:
    created = seeded.post(
        "/api/pizzas",
        json={"name": " margherita ", "chef_id": 1, "toppings": ["tomato sauce", "mozzarella"]},
    )
    assert created.status_code == 201, created.text
    pizza = created.json()
    assert pizza["name"] == "Margherita"
    assert pizza["chef"] == {"id": 1, "name": "Mario"}
    assert [t["name"] for t in pizza["toppings"]] == ["Mozzarella", "Tomato sauce"]

    got = seeded.get(f"/api/pizzas/{pizza['id']}")
    assert got.status_code == 200 and got.json() == pizza

    patched = seeded.patch(f"/api/pizzas/{pizza['id']}", json={"toppings": ["ham"]})
    assert patched.status_code == 200
    assert [t["name"] for t in patched.json()["toppings"]] == ["Ham"]
    assert patched.json()["chef"]["name"] == "Mario"

    assert seeded.delete(f"/api/pizzas/{pizza['id']}").status_code == 204
    assert seeded.get(f"/api/pizzas/{pizza['id']}").status_code == 404


def test_pizza_errors(seeded: TestClient) -> None:
    assert seeded.post("/api/pizzas", json={"name": "Ham"}).status_code == 201
    dup = seeded.post("/api/pizzas", json={"name": "ham"})
    assert dup.status_code == 409 and "already exists" in dup.json()["detail"]

    unknown = seeded.post("/api/pizzas", json={"name": "Fish", "toppings": ["anchovy"]})
    assert unknown.status_code == 422 and unknown.json()["detail"] == "Unknown toppings: Anchovy"

    assert seeded.post("/api/pizzas", json={"name": ""}).status_code == 422
    assert seeded.post("/api/pizzas", json={"name": "X", "chef_id": 42}).status_code == 422
    assert seeded.get("/api/pizzas/999").json() == {"detail": "Pizza 999 does not exist."}
    assert seeded.get("/api/pizzas/abc").status_code == 422
    assert seeded.delete("/api/pizzas/999").status_code == 404


def test_pizza_list_pagination_and_filters(seeded: TestClient) -> None:
    for name, tops in [("A", ["ham"]), ("B", ["basil"]), ("C", ["ham", "basil"])]:
        seeded.post("/api/pizzas", json={"name": name, "toppings": tops})

    page = seeded.get("/api/pizzas", params={"limit": 2})
    assert page.headers["X-Total-Count"] == "3"
    body = page.json()
    assert [p["name"] for p in body["items"]] == ["A", "B"]
    assert body | {"items": None} == {"items": None, "total": 3, "limit": 2, "offset": 0}

    ham = seeded.get("/api/pizzas", params={"topping": "ham"}).json()
    assert [p["name"] for p in ham["items"]] == ["A", "C"]
    assert seeded.get("/api/pizzas", params={"limit": 0}).status_code == 422


def test_chefs_and_toppings(seeded: TestClient) -> None:
    assert [c["name"] for c in seeded.get("/api/chefs").json()] == ["Mario"]
    assert seeded.post("/api/chefs", json={"name": "mario"}).status_code == 409
    toppings = [t["name"] for t in seeded.get("/api/toppings").json()]
    assert toppings == ["Basil", "Ham", "Mozzarella", "Tomato sauce"]


# --- background work -------------------------------------------------------------------------


def wait_for_task(client: TestClient, task_id: str, timeout: float = 5.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = client.get(f"/api/tasks/{task_id}").json()
        if status["status"] != "pending":
            return status
        time.sleep(0.02)
    raise AssertionError("task did not finish")


def test_bake_job_runs_in_process(seeded: TestClient) -> None:
    pizza = seeded.post("/api/pizzas", json={"name": "Calzone"}).json()
    queued = seeded.post(f"/api/pizzas/{pizza['id']}/bake", json={"seconds": 0})
    assert queued.status_code == 202
    status = wait_for_task(seeded, queued.json()["task_id"])
    assert status == {
        "task_id": queued.json()["task_id"],
        "status": "success",
        "result": "Calzone is ready after 0s in the oven.",
        "error": None,
    }


def test_bake_validation(seeded: TestClient) -> None:
    assert seeded.post("/api/pizzas/99/bake").status_code == 404
    pizza = seeded.post("/api/pizzas", json={"name": "Calzone"}).json()
    assert seeded.post(f"/api/pizzas/{pizza['id']}/bake", json={"seconds": 600}).status_code == 422
    # no body at all uses the default baking time
    assert seeded.post(f"/api/pizzas/{pizza['id']}/bake").status_code == 202


def test_unknown_task_is_pending(client: TestClient) -> None:
    assert client.get("/api/tasks/nope").json()["status"] == "pending"


def test_background_messages(client: TestClient, settings: Settings) -> None:
    assert client.get("/api/tasks/messages").json() == []
    for msg in ("first", "second", "third"):
        assert client.post("/api/tasks/messages", json={"message": msg}).status_code == 202
    assert settings.message_log.read_text().splitlines() == ["first", "second", "third"]
    assert client.get("/api/tasks/messages", params={"last": 2}).json() == ["second", "third"]
    assert client.post("/api/tasks/messages", json={"message": "  "}).status_code == 422


# --- files ----------------------------------------------------------------------------------


def test_upload_list_download(client: TestClient, settings: Settings) -> None:
    files = {"file": ("../../evil name.pdf", b"%PDF-1.7 hello", PDF)}
    up = client.post("/api/files", files=files)
    assert up.status_code == 201
    assert up.json() == {"name": "evil_name.pdf", "size": 14, "content_type": PDF}
    assert (settings.upload_dir / "evil_name.pdf").read_bytes() == b"%PDF-1.7 hello"

    again = client.post("/api/files", files=files).json()
    assert again["name"] == "evil_name-1.pdf"

    listing = client.get("/api/files").json()
    assert [f["name"] for f in listing] == ["evil_name-1.pdf", "evil_name.pdf"]

    download = client.get("/api/files/evil_name.pdf")
    assert download.status_code == 200 and download.content == b"%PDF-1.7 hello"
    assert client.get("/api/files/..%2Fsecrets").status_code == 404


def test_upload_rejections(client: TestClient, settings: Settings) -> None:
    bad_type = client.post("/api/files", files={"file": ("a.png", b"x", "image/png")})
    assert bad_type.status_code == 415

    too_big = client.post("/api/files", files={"file": ("big.pdf", b"x" * 2048, PDF)})
    assert too_big.status_code == 413
    assert not any(settings.upload_dir.iterdir())  # partial file removed

    assert client.post("/api/files").status_code == 422


def test_xlsx_preview(client: TestClient, settings: Settings, tmp_path: Path) -> None:
    settings.max_upload_bytes = 1_000_000
    wb = Workbook()
    wb.active.append(["Country", "Units"])
    for i in range(8):
        wb.active.append([f"C{i}", i])
    path = tmp_path / "sales.xlsx"
    wb.save(path)

    up = client.post("/api/files", files={"file": ("sales.xlsx", path.read_bytes(), XLSX)})
    assert up.status_code == 201

    preview = client.get("/api/files/sales.xlsx/preview", params={"rows": 2}).json()
    assert preview["header"] == ["Country", "Units"]
    assert preview["rows"] == [["C0", 0], ["C1", 1]]
    assert preview["total_rows"] == 8

    client.post("/api/files", files={"file": ("doc.pdf", b"%PDF", PDF)})
    assert client.get("/api/files/doc.pdf/preview").status_code == 415
    assert client.get("/api/files/missing.xlsx/preview").status_code == 404


# --- misc -----------------------------------------------------------------------------------


def test_health_ok(client: TestClient) -> None:
    response = client.get("/api/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok" and response.json()["database"] == "ok"


def test_health_reports_broken_database(settings: Settings, tmp_path: Path) -> None:
    settings.database_url = f"sqlite+aiosqlite:///{tmp_path}"  # a directory, not a db file
    with TestClient(create_app(settings, http_client=httpx2.AsyncClient())) as c:
        response = c.get("/api/healthz")
    assert response.status_code == 503
    assert response.json()["database"] == "unavailable"


@pytest.mark.parametrize(
    ("todo", "status", "detail"),
    [
        (1, 200, None),
        (404, 404, "Upstream resource '/todos/404' not found."),
        (500, 502, "Upstream answered 500."),
        (503, 502, "Upstream request failed: ConnectError"),
        (2, 502, "Upstream did not return JSON."),
    ],
)
def test_external_call(client: TestClient, todo: int, status: int, detail: str | None) -> None:
    response = client.get(f"/api/external/todos/{todo}")
    assert response.status_code == status
    if detail is None:
        assert response.json()["title"] == "delectus aut autem"
    else:
        assert response.json()["detail"] == detail


def test_request_id_and_timing_headers(client: TestClient) -> None:
    response = client.get("/api/healthz", headers={"X-Request-ID": "trace-42"})
    assert response.headers["X-Request-ID"] == "trace-42"
    assert response.headers["X-Process-Time"].endswith("ms")
    fresh = client.get("/api/healthz")
    assert len(fresh.headers["X-Request-ID"]) == 32


def test_cors_preflight_for_vite_dev_server(client: TestClient) -> None:
    response = client.options(
        "/api/pizzas",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_index_page_and_static(seeded: TestClient) -> None:
    seeded.post("/api/pizzas", json={"name": "Hawaiian", "toppings": ["ham"]})
    page = seeded.get("/")
    assert page.status_code == 200
    assert "Hawaiian" in page.text and "1 pizza in the database" in page.text
    assert seeded.get("/static/js/chat.js").status_code == 200


def test_websocket_echo(client: TestClient) -> None:
    with client.websocket_connect("/ws/echo") as ws:
        ws.send_text("hi")
        assert ws.receive_text() == "Message text was: hi"


def test_openapi_schema(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/api/pizzas", "/api/pizzas/{pizza_id}/bake", "/api/files"} <= paths.keys()


@pytest.mark.anyio
async def test_async_client_with_asgi_transport(settings: Settings, schema: None) -> None:
    """The same app driven by ``httpx2.AsyncClient`` in the test's own event loop."""
    app = create_app(settings, http_client=httpx2.AsyncClient())
    async with app.router.lifespan_context(app):
        transport = httpx2.ASGITransport(app=app)
        async with httpx2.AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.post("/api/toppings", json={"name": "ham"})
            created = await ac.post("/api/pizzas", json={"name": "Async", "toppings": ["Ham"]})
            assert created.status_code == 201
            queued = await ac.post(f"/api/pizzas/{created.json()['id']}/bake", json={"seconds": 0})
            await app.state.broker.wait_all()
            status = (await ac.get(f"/api/tasks/{queued.json()['task_id']}")).json()
            assert status["status"] == "success"
