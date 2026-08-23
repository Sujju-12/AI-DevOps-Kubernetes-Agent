# Prompt 04 — Dashboard and Supabase

Users sign in with **Supabase Auth**, click **Investigate Cluster**, watch live progress, then see diagnosis and history.

FastAPI still runs kubectl + AI. Supabase stores sessions, progress, and history.

## What you need

1. In [Auth settings](https://supabase.com/dashboard/project/tzdxvhbdpkqckkmecytz/auth/providers) enable Email login. For local demos, turn off **Confirm email**.
2. Copy the anon key from **Project Settings → API** into:

```env
# backend/.env
SUPABASE_URL=https://tzdxvhbdpkqckkmecytz.supabase.co
SUPABASE_ANON_KEY=

# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://tzdxvhbdpkqckkmecytz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

3. `docker compose up --build` (pass the same `NEXT_PUBLIC_SUPABASE_ANON_KEY` / `SUPABASE_ANON_KEY` so the frontend image can bake the public key).

## Flow

1. User signs in (or signs up) in the UI.
2. The dashboard inserts a row into `public.investigations` (RLS: own rows only).
3. The UI subscribes to Supabase Realtime on that table.
4. `POST /investigate` runs with `Authorization: Bearer <access_token>` and `investigation_id`.
5. The backend updates `steps` / diagnosis on that row; the UI refreshes live.
6. Recent rows appear under **Recent Investigations**.

Unauthenticated `POST /investigate` still works for scripts and tests (no history write).

## Schema

Applied on project `tzdxvhbdpkqckkmecytz` (see `supabase/migrations/20260823120000_create_investigations.sql`).
