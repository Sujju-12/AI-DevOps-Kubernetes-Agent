# Prompt 04 — Dashboard and Supabase

Users sign in with **Supabase Auth**, click **Investigate Cluster**, watch live progress, then see diagnosis and history.

FastAPI still runs kubectl + AI. Supabase stores sessions, progress, and history.

## What you need

1. In [Auth settings](https://supabase.com/dashboard/project/tzdxvhbdpkqckkmecytz/auth/providers) enable Email login. For local demos, turn off **Confirm email**.
2. This repo already ships the **publishable anon key** for project `tzdxvhbdpkqckkmecytz` (in `frontend/.env.example`, Docker defaults, and `next.config.js`). For a local Next.js run:

```bash
cp frontend/.env.example frontend/.env.local
cd frontend && npm install && npm run dev
```

Or from the repo root: `docker compose up --build`.

To use a different Supabase project, copy keys from **Project Settings → API** into `frontend/.env.local` and `backend/.env`. Never commit the service role key.

3. `docker compose up --build` bakes the public anon key into the frontend image.

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
