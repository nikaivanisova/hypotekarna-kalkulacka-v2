# Backend (Python)

Parsing, validation and the mortgage calculation, served over HTTP with FastAPI; writes to Supabase.

- **Phase 2:** port of the V1 domain (`legacy/cli/src/domain`, `input`, `app`) to `mortgage/` with pytest, reproducing every V1 expected value.
- **Phase 4:** the API routes. **Phase 6:** Supabase persistence. **Phase 7:** extra payments (`domain/schedule.py`).

Tooling: Python 3.14 and `uv` (`uv run pytest`).
