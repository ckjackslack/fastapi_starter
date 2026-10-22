"""fastapi_starter: a small, current FastAPI project template."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fastapi-starter")
except PackageNotFoundError:  # pragma: no cover - running from a source checkout
    __version__ = "0.0.0"
