# AGENTS.md

## Supabase backend

This project uses [Supabase](https://supabase.com) for authentication, Postgres, realtime, and investigation history (Prompt 04+). FastAPI remains the Kubernetes investigation orchestrator.

- **Project ref:** `tzdxvhbdpkqckkmecytz`
- **API URL:** `https://tzdxvhbdpkqckkmecytz.supabase.co`
- **MCP:** Cursor loads `.cursor/mcp.json` (hosted Supabase MCP with docs, account, database, debugging, development, functions, and branching).
- **Skills:** installed from [`supabase/agent-skills`](https://github.com/supabase/agent-skills) via `npx skills add supabase/agent-skills` (see `skills-lock.json`). Load these before implementing Supabase features:
  - `supabase`: Database, Auth, Edge Functions, Realtime, Storage, CLI/MCP, RLS, and debugging.
  - `supabase-postgres-best-practices`: schema, migrations, indexes, RLS, and query design.
- **Credentials:** app code reads `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and optional `SUPABASE_SERVICE_ROLE_KEY` from env. Never hardcode or commit keys. The service role key is backend-only.

When working on database, auth, RLS, or Edge Functions, use the **Supabase MCP** tools and the skills above instead of guessing the API.

Key patterns:

- Reference users with `auth.users(id)`; use `auth.uid()` in RLS policies.
- Prefer the anon key in the browser; use the service role only on the FastAPI server.
- Enable RLS on every table in an exposed schema (`public` by default).

