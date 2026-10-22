"""File uploads (PDF / CSV / XLSX by default), listing, download and spreadsheet preview."""

from typing import Annotated

from fastapi import APIRouter, Query, UploadFile, status
from fastapi.responses import FileResponse

from ..errors import UnsupportedMediaError
from ..schemas import SheetPreview, StoredFile
from ..services import storage
from ..services.spreadsheet import preview_workbook
from .deps import SettingsDep

router = APIRouter(prefix="/files", tags=["files"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload(file: UploadFile, settings: SettingsDep) -> StoredFile:
    storage.check_content_type(file.content_type, settings.allowed_upload_types)
    path, size = await storage.save_upload(file, settings.upload_dir, settings.max_upload_bytes)
    return StoredFile(name=path.name, size=size, content_type=file.content_type)


# Plain ``def`` endpoints: FastAPI runs them in a worker thread, fine for blocking file I/O.
@router.get("")
def list_uploads(settings: SettingsDep) -> list[StoredFile]:
    return [
        StoredFile(name=n, size=s, content_type=t)
        for n, s, t in storage.list_files(settings.upload_dir)
    ]


@router.get("/{name}")
def download(name: str, settings: SettingsDep) -> FileResponse:
    return FileResponse(storage.resolve_stored(settings.upload_dir, name), filename=name)


@router.get("/{name}/preview")
def preview(
    name: str,
    settings: SettingsDep,
    rows: Annotated[int, Query(ge=1, le=100)] = 5,
    sheet: str | None = None,
) -> SheetPreview:
    path = storage.resolve_stored(settings.upload_dir, name)
    if path.suffix.lower() != ".xlsx":
        raise UnsupportedMediaError("Preview is only available for .xlsx files.")
    return preview_workbook(path, rows=rows, sheet=sheet)
