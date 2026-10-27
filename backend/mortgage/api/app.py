"""The HTTP API (Phase 4): implements api/openapi.yaml exactly.

Run locally:  uv run python -m uvicorn mortgage.api.app:app --port 8000
Settings (environment):
    MORTGAGE_CORS_ORIGINS  comma-separated allowed origins (default: the Vite dev server)
"""
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

CONTRACT_PATH = Path(__file__).resolve().parents[3] / 'api' / 'openapi.yaml'
DEFAULT_CORS_ORIGINS = ['http://localhost:5173']


def cors_origins_from_env() -> list[str]:
    value = os.environ.get('MORTGAGE_CORS_ORIGINS')
    if value is None:
        return DEFAULT_CORS_ORIGINS
    return [origin.strip() for origin in value.split(',') if origin.strip()]


def create_app(cors_origins: list[str] | None = None) -> FastAPI:
    origins = cors_origins if cors_origins is not None else cors_origins_from_env()
    if '*' in origins:
        raise ValueError('CORS must list the frontend origin(s); "*" is not allowed (api/openapi.yaml).')

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
            return JSONResponse({'errors': [{'field': e.field, 'code': e.code} for e in outcome.errors]},
                                status_code=422)
        r = outcome.result
        return JSONResponse({
            'id': None,  # persistence arrives in Phase 6
            'numberOfPayments': r.number_of_payments,
            'regularPayment': str(r.regular_payment),
            'finalPayment': str(r.final_payment),
            'totalPaid': str(r.total_paid),
            'totalInterest': str(r.total_interest),
        })

    @app.get('/api/v1/health')
    async def health() -> JSONResponse:
        return JSONResponse({'status': 'ok'})

    return app


app = create_app()
