"""Domain errors raised by the service layer and mapped to HTTP responses in ``main``."""

from __future__ import annotations


class AppError(Exception):
    status_code = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class InvalidReferenceError(AppError):
    """A request refers to related objects (chef, toppings) that do not exist."""

    status_code = 422


class UnsupportedMediaError(AppError):
    status_code = 415


class PayloadTooLargeError(AppError):
    status_code = 413


class UpstreamError(AppError):
    status_code = 502
