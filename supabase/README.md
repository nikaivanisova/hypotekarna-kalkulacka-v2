# Supabase

Database schema as SQL migrations in `migrations/`, applied with the Supabase CLI. Added in **Phase 6** (the `calculations` table, plan §4).

Only the backend accesses the database (service role); row-level security is on with no public policies.
