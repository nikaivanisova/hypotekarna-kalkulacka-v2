"""RFC 9457 problem responses (api/openapi.yaml `Problem`; review 03 #3, #4).

`detail` may name a property, never a request value, and is dropped on 5xx.
"""
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

PROBLEM_JSON = 'application/problem+json'


def problem(status: int, detail: str | None = None, headers: dict[str, str] | None = None) -> JSONResponse:
    body: dict[str, object] = {'type': 'about:blank', 'title': HTTPStatus(status).phrase, 'status': status}
    if detail and status < 500:
        body['detail'] = detail
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON, headers=headers)


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    # Starlette's own detail is only the status phrase; the title already says that.
    return problem(exc.status_code, headers=exc.headers)


async def validation_exception_handler(_request: Request, _exc: RequestValidationError) -> JSONResponse:
    # No route uses a Pydantic body, so this is a safety net. FastAPI's default would echo the input.
    return problem(400)


async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return problem(500)


def install_problem_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
