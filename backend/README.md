# Backend (Python)

Parsing, validation and the mortgage calculation, served over HTTP with FastAPI; writes to Supabase.

| Phase | Status | Content |
|---|---|---|
| 2 | ✅ done | `mortgage/` — port of V1 M1–M4 and M7 (`domain/`, `input/`, `app/`), 123 tests |
| 4 | — | `mortgage/api/`: FastAPI routes |
| 6 | — | `mortgage/persistence/`: Supabase |
| 7 | — | `mortgage/domain/schedule.py`: extra payments |

## Run the tests

```bash
cd backend
uv sync
uv run python -m pytest
```

Use `python -m pytest`, not `uv run pytest`: Windows Application Control on the dev machine blocks the `pytest.exe` launcher in `.venv`.

## Layers

| Module | V1 | Rule |
|---|---|---|
| `domain/types.py` | M1 | Types only. API field names and error codes (camelCase) are used as-is. |
| `domain/calculation.py` | M4 | Private `Context(prec=40, ROUND_HALF_UP)` entered with `localcontext()`; the caller's context is never changed. |
| `input/parsing.py` | M2 | Strict grammar with `fullmatch` before `Decimal()`; trims exactly the JavaScript `trim()` whitespace set. |
| `input/validation.py` | M3 | Same rules, codes and order as V1; `-0` is `negative` (`is_signed()`). |
| `app/calculator.py` | M7 | Validation, then calculation. Returns data, no display text. |

`tests/test_architecture.py` enforces the allowed imports per layer, no I/O, and no cycles.

## Parity checks

- `tests/domain/test_reference_parity.py`: all 6 800 sweep loans equal `tools/reference.py` (exact rationals), cent for cent.
- `tools/v1_parity.py`: all 6 800 sweep loans equal the V1 TypeScript code in `legacy/cli` (run by hand).
