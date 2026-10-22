# API contract

`openapi.yaml` (OpenAPI 3.1) is the agreement between the frontend and the backend. It was written in Phase 3 of `docs/v2/00-refactor-plan.md` and reviewed in `docs/v2/03-api-review.md`.

- `POST /api/v1/calculations`: raw text in, results as 2-dp decimal strings out; `422` with error codes for invalid input; `400`/`413`/`415`/`429`/`500` as `application/problem+json`.
- `GET /api/v1/health`: liveness.

Money is always a decimal string (`"449.04"`), never a JSON number.

The contract is tested in `backend/tests/contract/test_openapi.py`: it must be valid OpenAPI, every example must be valid against its schema, and every request example must match the real backend.
