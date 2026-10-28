# Supabase

Project **`hypotekarna-kalkulacka`** (id `rncaqhekknjdivkpadkw`, region `eu-central-1`, free plan), created in Phase 6 (decision D11).

The schema lives as SQL migrations in `migrations/`. The file name is the version Supabase recorded when the migration was applied:

| Version | Migration | Content |
|---|---|---|
| `20261027221257` | `create_calculations` | `public.calculations` (FR-4), plan §4 plus CHECK constraints that mirror the V1 rules |
| `20261028205501` | `extra_payments` | Phase 7 (04 §5): `months_saved` and `interest_saved` (both `>= 0`) on `calculations`; table `extra_payments` (PK calculation + position, `used_amount ≤ amount`, cascade delete); function `save_calculation(payload jsonb) returns uuid` |

## Access

Only the backend reads or writes, using the **secret key** (`sb_secret_...`, in `backend/.env`; never in git or in the frontend):

- RLS is enabled with **no policies**. The security advisor reports this as INFO "RLS enabled, no policy"; that is intended.
- All privileges are revoked from `anon` and `authenticated`. Verified: `set role anon; select ...` → `permission denied`.

## `save_calculation` (Phase 7)

- Saves a calculation and its extra payments **in one transaction**, and checks each item's month against the loan's term.
- `security invoker`, `set search_path = ''`. EXECUTE is revoked from `public`, `anon` and `authenticated` and granted only to `service_role`.
- Verified on 2026-10-28:
  - `has_function_privilege`: anon false, authenticated false, service_role true.
  - With the publishable key, `/rest/v1/rpc/save_calculation` → HTTP 401, and both tables → `permission denied`.
  - As `service_role` in a rolled-back transaction, E3 saved 3 items in order with the right statuses.
  - A month beyond the term is rejected and nothing is written.
  - Security advisor: only the intended INFO "RLS enabled, no policy" for both tables.

## Constraints

The database rejects rows that break the calculation rules, even if the backend has a bug. Verified by inserting bad rows, which were rejected:

- input ranges: loan 1 000–1 000 000, rate 0–20, term 1–30
- `final_payment > 0`, `regular_payment > 0`, `total_interest >= 0`
- `number_of_payments` between 1 and `term_years × 12`
- `total_interest = total_paid − loan_amount`

## Changing the schema

Add a new migration file; never edit an applied one. Apply it with the Supabase CLI or the Supabase MCP `apply_migration` tool, then rename the file to the recorded version (`list_migrations`).
