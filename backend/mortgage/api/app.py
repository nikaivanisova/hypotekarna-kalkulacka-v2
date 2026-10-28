"""The HTTP API (Phase 4): implements api/openapi.yaml exactly.

Run locally:  uv run --env-file .env python -m uvicorn mortgage.api.app:app --port 8000
Settings (environment):
    MORTGAGE_CORS_ORIGINS  comma-separated allowed origins (default: the Vite dev server)
    SUPABASE_URL, SUPABASE_SECRET_KEY  where calculations are saved (mortgage/persistence; optional)
"""
import logging
import os
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mortgage.api.body_limit import BodySizeLimitMiddleware
from mortgage.api.problems import install_problem_handlers, problem
from mortgage.api.request import RequestError, parse_calculation_request
from mortgage.app.calculator import Rejected, run_calculator
from mortgage.persistence.repository import CalculationRepository, repository_from_env

CONTRACT_PATH = Path(__file__).resolve().parents[3] / 'api' / 'openapi.yaml'
DEFAULT_CORS_ORIGINS = ['http://localhost:5173']

log = logging.getLogger(__name__)


def cors_origins_from_env() -> list[str]:
    value = os.environ.get('MORTGAGE_CORS_ORIGINS')
    if value is None:
        return DEFAULT_CORS_ORIGINS
    return [origin.strip() for origin in value.split(',') if origin.strip()]


def error_body(error) -> dict[str, object]:
    """A ValidationError as the contract's object; index and property only for extraPayments items."""
    body: dict[str, object] = {'field': error.field, 'code': error.code}
    if error.index is not None:
        body['index'] = error.index
        body['property'] = error.property
    return body


async def save_best_effort(repository: CalculationRepository, outcome) -> str | None:
    """D5: a failed save never fails the request; the result is returned with id null."""
    try:
        return await repository.save(outcome.loan, outcome.result)
    except Exception as error:  # noqa: BLE001 — any repository bug must not turn a result into a 500
        log.warning('calculation not saved: %s', type(error).__name__)
        return None


def create_app(cors_origins: list[str] | None = None, repository: CalculationRepository | None = None) -> FastAPI:
    origins = cors_origins if cors_origins is not None else cors_origins_from_env()
    if '*' in origins:
        raise ValueError('CORS must list the frontend origin(s); "*" is not allowed (api/openapi.yaml).')
    repository = repository if repository is not None else repository_from_env()

    app = FastAPI(title='Mortgage Calculator API', redoc_url=None)
    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding='utf-8'))
    app.openapi = lambda: contract  # serve the reviewed contract, not FastAPI's generated document

    install_problem_handlers(app)
    # Added last = outermost: CORS headers are also set on 413 responses from the body limit.
    app.add_middleware(BodySizeLimitMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['GET', 'POST'],
                       allow_headers=['Content-Type'])

    @app.post('/api/v1/calculations')
    async def create_calculation(request: Request) -> JSONResponse:
        media_type = request.headers.get('content-type', '').split(';')[0].strip().lower()
        if media_type != 'application/json':
            return problem(415)
        try:
            raw = parse_calculation_request(await request.body())
        except RequestError as error:
            return problem(400, error.detail)

        outcome = run_calculator(raw)
        if isinstance(outcome, Rejected):
            return JSONResponse({'errors': [error_body(e) for e in outcome.errors]}, status_code=422)
        r = outcome.result
        return JSONResponse({
            'id': await save_best_effort(repository, outcome),
            'numberOfPayments': r.number_of_payments,
            'regularPayment': str(r.regular_payment),
            'finalPayment': str(r.final_payment),
            'totalPaid': str(r.total_paid),
            'totalInterest': str(r.total_interest),
            'monthsSaved': r.months_saved,
            'interestSaved': str(r.interest_saved),
            'extraPayments': [{'month': e.month, 'amount': str(e.amount), 'usedAmount': str(e.used_amount),
                               'status': e.status} for e in r.extra_payments],
        })

    @app.get('/api/v1/health')
    async def health() -> JSONResponse:
        return JSONResponse({'status': 'ok'})

    return app


app = create_app()
