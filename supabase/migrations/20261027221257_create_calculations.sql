-- FR-4: every successful calculation is saved (docs/v2/01-functional.md §2.2; plan §4).
-- Money and rates are numeric, never float. Values are stored as validated / as returned by the API.
create table public.calculations (
  id                 uuid primary key default gen_random_uuid(),
  created_at         timestamptz   not null default now(),
  loan_amount        numeric(12,2) not null check (loan_amount between 1000 and 1000000),
  annual_rate        numeric(5,2)  not null check (annual_rate between 0 and 20),
  term_years         smallint      not null check (term_years between 1 and 30),
  number_of_payments smallint      not null,
  regular_payment    numeric(12,2) not null check (regular_payment > 0),
  final_payment      numeric(12,2) not null check (final_payment > 0),
  total_paid         numeric(14,2) not null,
  total_interest     numeric(14,2) not null check (total_interest >= 0),
  engine_version     text          not null check (length(engine_version) between 1 and 40),
  -- Cross-column rules (V1 01 §4.4–4.5): the same invariants the backend's sweep test checks.
  constraint calculations_payments_within_term check (number_of_payments between 1 and term_years * 12),
  constraint calculations_interest_is_paid_minus_loan check (total_interest = total_paid - loan_amount)
);

comment on table public.calculations is
  'FR-4: one row per successful calculation. Written only by the backend (secret key); no public access.';

-- Only the backend may read or write (decision D4). RLS with no policies blocks the anon and
-- authenticated roles; revoking their privileges is a second layer. The secret key bypasses both.
alter table public.calculations enable row level security;
revoke all on table public.calculations from anon, authenticated;
