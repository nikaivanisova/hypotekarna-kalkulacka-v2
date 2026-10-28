-- Phase 7: extra payments (docs/v2/04-extra-payments.md §5; review docs/v2/05-extra-payments-review.md #3, #6).
-- Additive: existing rows get months_saved 0 and interest_saved 0, which is correct for them (no extras).

alter table public.calculations
  add column months_saved   smallint      not null default 0 check (months_saved >= 0),
  add column interest_saved numeric(14,2) not null default 0 check (interest_saved >= 0);

create table public.extra_payments (
  calculation_id uuid          not null references public.calculations(id) on delete cascade,
  position       smallint      not null check (position between 0 and 9),
  month          smallint      not null check (month between 1 and 360),
  amount         numeric(12,2) not null check (amount between 0.01 and 1000000),
  used_amount    numeric(12,2) not null,
  status         text          not null check (length(status) between 1 and 40),
  primary key (calculation_id, position),
  constraint extra_payments_used_within_amount check (used_amount between 0 and amount)
);

comment on table public.extra_payments is
  'FR-5: the extra payments of a saved calculation, in request order. Written only by save_calculation.';

alter table public.extra_payments enable row level security;
revoke all on table public.extra_payments from anon, authenticated;

-- Saves a calculation and its extra payments in one transaction (a PostgREST RPC call is one
-- transaction; any error rolls everything back). Money arrives as JSON strings, never floats.
-- security invoker: the caller's rights apply. Only service_role (the secret key, which bypasses
-- RLS) may execute it; PUBLIC's default EXECUTE and Supabase's default grants are revoked below.
create function public.save_calculation(payload jsonb)
returns uuid
language plpgsql
security invoker
set search_path = ''
as $$
declare
  items  jsonb := coalesce(payload -> 'extra_payments', '[]'::jsonb);
  new_id uuid;
begin
  if jsonb_typeof(items) <> 'array' or jsonb_array_length(items) > 10 then
    raise exception 'extra_payments must be an array of at most 10 items' using errcode = '22023';
  end if;
  -- The table can only check 1 to 360; the month must also be within this loan's term.
  if exists (select 1 from jsonb_array_elements(items) as e(value)
             where (e.value ->> 'month')::int > (payload ->> 'term_years')::int * 12) then
    raise exception 'extra payment month beyond the term' using errcode = '22023';
  end if;

  insert into public.calculations (loan_amount, annual_rate, term_years, number_of_payments, regular_payment,
                                   final_payment, total_paid, total_interest, months_saved, interest_saved,
                                   engine_version)
  values ((payload ->> 'loan_amount')::numeric, (payload ->> 'annual_rate')::numeric,
          (payload ->> 'term_years')::smallint, (payload ->> 'number_of_payments')::smallint,
          (payload ->> 'regular_payment')::numeric, (payload ->> 'final_payment')::numeric,
          (payload ->> 'total_paid')::numeric, (payload ->> 'total_interest')::numeric,
          (payload ->> 'months_saved')::smallint, (payload ->> 'interest_saved')::numeric,
          payload ->> 'engine_version')
  returning id into new_id;

  -- Positions come from the array order, so they are 0 .. count - 1 without gaps.
  insert into public.extra_payments (calculation_id, position, month, amount, used_amount, status)
  select new_id, (e.ordinality - 1)::smallint, (e.value ->> 'month')::smallint, (e.value ->> 'amount')::numeric,
         (e.value ->> 'used_amount')::numeric, e.value ->> 'status'
  from jsonb_array_elements(items) with ordinality as e(value, ordinality);

  return new_id;
end;
$$;

revoke execute on function public.save_calculation(jsonb) from public, anon, authenticated;
grant execute on function public.save_calculation(jsonb) to service_role;
