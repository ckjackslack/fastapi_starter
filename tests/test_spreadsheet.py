from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import Workbook

from fastapi_starter.errors import UnsupportedMediaError
from fastapi_starter.services.spreadsheet import preview_workbook


def make_workbook(path: Path, rows: int = 10) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Sales"
    ws.append(["Country", "Year", "Units", "Date"])
    for i in range(rows):
        ws.append([f"Country {i}", 2020 + i % 3, i * 10, date(2024, 1, 1 + i)])
    other = wb.create_sheet("Notes")
    other.append(["note"])
    other.append(["hello"])
    wb.save(path)
    return path


def test_preview_active_sheet(tmp_path: Path) -> None:
    preview = preview_workbook(make_workbook(tmp_path / "s.xlsx"), rows=3)
    assert preview.sheet == "Sales"
    assert preview.header == ["Country", "Year", "Units", "Date"]
    assert len(preview.rows) == 3
    assert preview.rows[0] == ["Country 0", 2020, 0, "2024-01-01T00:00:00"]
    assert preview.total_rows == 10
    assert preview.total_columns == 4


def test_preview_named_sheet_and_short_sheet(tmp_path: Path) -> None:
    preview = preview_workbook(make_workbook(tmp_path / "s.xlsx"), rows=50, sheet="Notes")
    assert preview.header == ["note"] and preview.rows == [["hello"]]


def test_preview_unknown_sheet(tmp_path: Path) -> None:
    with pytest.raises(UnsupportedMediaError, match="Available: Sales, Notes"):
        preview_workbook(make_workbook(tmp_path / "s.xlsx"), sheet="Nope")


def test_preview_rejects_non_workbooks() -> None:
    with pytest.raises(UnsupportedMediaError):
        preview_workbook(BytesIO(b"definitely not a zip"))
