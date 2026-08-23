# Supabase configuration

Auth, history, and realtime (later prompts) use this Supabase project. FastAPI stays the investigation orchestrator.

## Project

| | |
|---|---|
| Project ref | `tzdxvhbdpkqckkmecytz` |
| API URL | `https://tzdxvhbdpkqckkmecytz.supabase.co` |

Dashboard: https://supabase.com/dashboard/project/tzdxvhbdpkqckkmecytz

## Cursor MCP

This repo ships `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "supabase": {
      "url": "https://mcp.supabase.com/mcp?project_ref=tzdxvhbdpkqckkmecytz&features=docs%2Caccount%2Cdatabase%2Cdebugging%2Cdevelopment%2Cfunctions%2Cbranching"
    }
  }
}
```

In Cursor: **Settings → MCP**, confirm the `supabase` server is enabled, then complete the Supabase login if prompted. Features enabled: docs, account, database, debugging, development, functions, branching.

## Agent skills

Installed with:

```bash
npx skills add supabase/agent-skills
```

That writes `skills-lock.json` and copies skills into `.agents/skills/` (gitignored). Re-run the same command after clone. Skills:

- `supabase` — Database, Auth, Edge Functions, Realtime, Storage, CLI/MCP, RLS
- `supabase-postgres-best-practices` — schema, migrations, indexes, RLS, query design

## Environment variables

Copy `backend/.env.example` and `frontend/.env.example`. Put secrets only in local `.env` files (gitignored).

```env
SUPABASE_URL=https://tzdxvhbdpkqckkmecytz.supabase.co
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4o-mini
```

Frontend (public anon key only):

```env
NEXT_PUBLIC_SUPABASE_URL=https://tzdxvhbdpkqckkmecytz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_SUPABASE_PROJECT_REF=tzdxvhbdpkqckkmecytz
```

Get keys from **Project Settings → API**. Never commit the service role key.

Docker Compose forwards `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` into the backend container.
