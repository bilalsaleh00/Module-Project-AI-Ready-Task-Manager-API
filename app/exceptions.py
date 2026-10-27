from fastapi import Request
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class DuplicateError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


async def not_found_handler(
    request: Request,
    exc: NotFoundError
):
    return JSONResponse(
        status_code=404,
        content={
            "error": "NotFoundError",
            "message": exc.detail,
            "status_code": 404
        }
    )


async def duplicate_handler(
    request: Request,
    exc: DuplicateError
):
    return JSONResponse(
        status_code=409,
        content={
            "error": "DuplicateError",
            "message": exc.detail,
            "status_code": 409
        }
    )