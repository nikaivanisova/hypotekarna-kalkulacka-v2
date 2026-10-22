# Mortgage Calculator

A fixed-rate annuity mortgage calculator: monthly payment, final payment, total paid and total interest from the loan amount, interest rate and term.

V2 is being refactored into four parts (plan: [`docs/v2/00-refactor-plan.md`](docs/v2/00-refactor-plan.md)):

| Folder | Part |
|---|---|
| `frontend/` | Web page (JavaScript) |
| `api/` | API contract (OpenAPI) |
| `backend/` | Calculations and API server (Python) |
| `supabase/` | Database migrations |
| `tools/` | `reference.py`: exact-rational reference for the calculation (`py -I tools/reference.py`) |
| `legacy/cli/` | V1, the TypeScript command-line version |
