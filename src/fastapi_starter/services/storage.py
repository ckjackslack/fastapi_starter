"""Safe file storage for uploads (the original wrote ``file.filename`` verbatim: path traversal)."""

from __future__ import annotations

import mimetypes
import re
import unicodedata
from pathlib import Path

import anyio
import anyio.to_thread
from fastapi import UploadFile

from ..errors import NotFoundError, PayloadTooLargeError, UnsupportedMediaError

CHUNK_SIZE = 64 * 1024
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: str | None, default: str = "upload") -> str:
    """Reduce an untrusted client filename to a safe basename.

    >>> safe_filename("../../etc/passwd")
    'passwd'
    >>> safe_filename("Financial Sample (1).xlsx")
    'Financial_Sample_1_.xlsx'
    """
    name = (name or "").replace("\\", "/").rsplit("/", 1)[-1]
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = _UNSAFE.sub("_", name).strip("._")
    return name[:120] or default


def unique_path(directory: Path, filename: str) -> Path:
    """Return ``directory/filename``, adding ``-1``, ``-2``... before the suffix if taken."""
    candidate = directory / filename
    stem, suffix = Path(filename).stem, Path(filename).suffix
    counter = 1
    while candidate.exists():
        candidate = directory / f"{stem}-{counter}{suffix}"
        counter += 1
    return candidate


def check_content_type(content_type: str | None, allowed: list[str]) -> None:
    base = (content_type or "").split(";")[0].strip().lower()
    if base not in {a.lower() for a in allowed}:
        raise UnsupportedMediaError(
            f"Content type {base or 'unknown'!r} is not allowed. Allowed: {', '.join(allowed)}"
        )


def _prepare_target(directory: Path, filename: str | None) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    return unique_path(directory, safe_filename(filename))


async def save_upload(file: UploadFile, directory: Path, max_bytes: int) -> tuple[Path, int]:
    """Stream an upload to disk, enforcing ``max_bytes``. Returns (stored path, size)."""
    target = await anyio.to_thread.run_sync(_prepare_target, directory, file.filename)
    written = 0
    try:
        async with await anyio.open_file(target, "xb") as out:
            while chunk := await file.read(CHUNK_SIZE):
                written += len(chunk)
                if written > max_bytes:
                    raise PayloadTooLargeError(f"File is larger than {max_bytes} bytes.")
                await out.write(chunk)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return target, written


def list_files(directory: Path) -> list[tuple[str, int, str | None]]:
    if not directory.is_dir():
        return []
    return [
        (p.name, p.stat().st_size, mimetypes.guess_type(p.name)[0])
        for p in sorted(directory.iterdir())
        if p.is_file()
    ]


def resolve_stored(directory: Path, name: str) -> Path:
    """Map a public file name back to a stored path, refusing anything outside ``directory``."""
    if safe_filename(name) != name:
        raise NotFoundError(f"File {name!r} not found.")
    path = directory / name
    if not path.is_file():
        raise NotFoundError(f"File {name!r} not found.")
    return path
