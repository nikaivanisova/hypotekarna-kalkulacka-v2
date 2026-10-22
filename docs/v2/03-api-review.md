# 03 — API Contract Review (Phase 3)

Status: **All findings resolved** (2026-10-22). Waiting for the author's approval of `api/openapi.yaml`.

An independent reviewer (a separate agent that had not written the contract) reviewed `api/openapi.yaml` against `backend/mortgage`, the V1/V2 specs and the plan, using the Layer 4 rules: "you did not write this", run things, do not estimate. The verdict was **approve with changes**: 5 Major, 8 Minor findings, no Blocker.

## What the reviewer verified by running code

- A sweep of 200 008 valid inputs (8 edge cases plus 200 000 random ones) through `run_calculator`. Every result matched the `Money` pattern and was never negative, and `finalPayment > 0` held (minimum 1.65, at 0 %). `1 ≤ numberOfPayments ≤ term × 12` held, `totalPaid` = regular × (n − 1) + final exactly, and `totalInterest` = totalPaid − principal exactly. The largest case (1 000 000, 20 %, 30 y) gives totalPaid 6015596.31.
- Error order and codes, and `null` / absent / empty / whitespace → `required`, all match the backend.
- A throwaway FastAPI/Pydantic v2 app (outside the repo) showed how FastAPI's defaults behave against the contract (findings #3, #4).

## Findings and resolutions

| # | Sev. | Finding | Resolution |
|---|---|---|---|
| 1 | Major | Response schemas had `additionalProperties: false`, so the "additive" Phase 7 result fields would break validating clients. | Response schemas are open; "clients MUST ignore unknown response properties". The request stays closed. Test: `test_contract_request_is_closed_and_responses_are_open`. |
| 2 | Major | The error vocabulary was closed (`enum`s, `maxItems: 3`, a fixed field order), so Phase 7 errors could not be added without breaking it. | `Field` and `ValidationErrorCode` are open strings that list their known values as `examples`. Clients show a generic message for unknown values. `maxItems` was removed. An `index` property is reserved for `extraPayments` items. A test checks that the known values equal the backend types. |
| 3 | Major | The 400/422 split is the opposite of FastAPI's defaults (FastAPI returns 422 `{"detail": [...]}` for malformed requests and generates its own OpenAPI). | The contract now says Phase 4 MUST install exception handlers and serve this YAML as the app's OpenAPI. Added `415` for a non-JSON Content-Type. The plan's Phase 4 "done when" is now "API tests prove conformance to `openapi.yaml`". |
| 4 | Major | FastAPI's default 422 echoes input values, and `{"loanAmount":"\ud800"}` crashes it into a plain-text 500. | `Problem.detail` never contains request values, and `500` has no `detail`. A lone surrogate is a listed `400` case. Phase 4 must test `\ud800`. |
| 5 | Major | There was no body-size limit, `429` or CORS note on an anonymous endpoint that writes a row on every request. | 1 KiB body limit (enforced before parsing) → `413`. Documented `429` with `Retry-After` (the policy is configuration, Phase 4/8). CORS: an allowlist of the frontend origin only. |
| 6 | Minor | "A 400 is never a user mistake" only holds if the frontend limits input length. | The frontend MUST set `maxlength="100"`. UTF-16 units ≥ code points, so the browser limit is the stricter one. |
| 7 | Minor | The `RawInput` description overstated which spaces are accepted. | Reworded: only U+0020 is allowed inside a number; trimming uses the JS `trim` set; NBSP/U+202F inside → `not_a_number` (relevant to `Intl.NumberFormat('sk-SK')` output). |
| 8 | Minor | The `totalPaid` formula and the `numberOfPayments` wording would become wrong in Phase 7. | Defined as "the sum of all payments made; without extra payments = …". Early ending can also be caused by extra payments. |
| 9 | Minor | An old server with a new client gives a hard 400. | Kept the closed request (it catches typos). The frontend omits an empty `extraPayments`, and frontend and backend deploy together. |
| 10 | Minor | `id: null` covered only a database outage. | Also covers "persistence not configured" (Phases 4–5). |
| 11 | Minor | Client handling of 400/500 and Money was not specified. | Status → client behaviour table in `info.description`. Clients must not do arithmetic on Money. |
| 12 | Minor | Error and health examples were not validated, and transitive test dependencies were not pinned. | Every example in the document is validated against its schema. `jsonschema`, `openapi-schema-validator` and `referencing` are pinned exactly. |
| 13 | Minor | `servers` listed only `http://localhost:8000`. | `url: /` (same origin); the local port is in the description. |

## Result

- `api/openapi.yaml` is valid OpenAPI 3.1.0.
- `backend/tests/contract/test_openapi.py` has 37 tests. All pass: every example is valid against its schema, every request example matches the real backend, and money is never a number.
- Backend total: 160 passed.
