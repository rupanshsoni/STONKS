# DEPLOYMENT — Vercel + Render + Env

> Two deploy surfaces: the web app (Vercel) and the desk worker (Render free tier, kept awake during market hours). Zero-cost hackathon setup.

## 1. Topology

```
Browser ──▶ Vercel (apps/web — Next.js 15)
              │  fetch initial state + SSE
              ▼
           Render (stonks worker — FastAPI on Python 3.11)
              │  always-on during market hours (cron ping)
              ├──▶ Alpaca paper (REST + WS)
              ├──▶ uvx alpaca-mcp-server (stdio subprocess)
              ├──▶ alpaca CLI (bundled in image)
              └──▶ LLMs: Gemini / OpenAI / Featherless
```

## 2. Desk worker (Render)

- **Service type:** Web Service (needed for a public HTTP URL for SSE) — free instance type.
- **Build:** `pip install -r requirements.txt` (Python 3.11); the `alpaca` CLI binary is downloaded and pinned in the Dockerfile/Build step (checksum-verified download from github.com/alpacahq/cli releases; Render native env → do it in a build script).
- **Start command:** `uvicorn stonks.api:app --host 0.0.0.0 --port $PORT`
- **Health check path:** `/health` (checks: DB reachable, Alpaca clock fetched within 10 min, MCP subprocess alive).
- **Sleep mitigation (free tier sleeps after 15 min idle):**
  - Frontend pings `/health` on load and every 5 min while a tab is open.
  - UptimeRobot (or cron-job.org) pings every 10 min, 13:30–20:00 UTC (US market hours) — outside those hours sleeping is *desired* (the desk is sleeping too).
  - GitHub Actions fallback: a scheduled workflow (every 30 min, market hours) hits `/health` and, if the wake handshake reports a REST/CLI mismatch, files an issue — redundancy at zero cost.

### render.yaml (checked into repo)

```yaml
services:
  - type: web
    name: stonks-desk
    runtime: python
    plan: free
    buildCommand: ./scripts/build-worker.sh   # pip install + pinned alpaca CLI
    startCommand: uvicorn stonks.api:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: ALPACA_MODE
        value: paper
      - key: ALPACA_API_KEY
        sync: false
      - key: ALPACA_SECRET_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: FEATHERLESS_API_KEY
        sync: false
      - key: PYTHON_VERSION
        value: "3.11.9"
```

## 3. Web app (Vercel)

- Import `apps/web` as the root; framework auto-detected (Next.js); build `pnpm build`.
- Env vars: `NEXT_PUBLIC_DESK_URL` (the Render URL), `NEXT_PUBLIC_WS_NOTE` (n/a — SSE only).
- `vercel.json`: rewrites nothing; CORS is handled worker-side (allow the Vercel domain).
- SSE on Vercel: the browser connects **directly to the Render URL** (Vercel functions don't hold long-lived streams) — the Next app proxies only the initial state fetch.

## 4. Environment variables (complete list)

| Var | Where | Notes |
|---|---|---|
| `ALPACA_MODE` | worker | must be `paper` (guard-tested) |
| `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` | worker | paper-trading keys |
| `GEMINI_API_KEY` | worker | Senti, debate researchers, narrator |
| `OPENAI_API_KEY` | worker | Verdi, Sage |
| `FEATHERLESS_API_KEY` | worker | partner-model analyst role |
| `DESK_PUBLIC_URL` | worker | self-reference for SSE origin headers |
| `CORS_ALLOW_ORIGIN` | worker | the Vercel domain |
| `NEXT_PUBLIC_DESK_URL` | Vercel | worker URL for the browser |

`.env.example` documents all of these with placeholder values; real values only in Render/Vercel dashboards (never in git).

## 5. Operational runbook (during the scoring window)

- **Morning (pre-open):** check `/health` green, journal shows overnight reconcile entries, UptimeRobot active.
- **Market open:** verify cycle events flowing in journal + SSE; the desk should journal `RECONCILE_OK` each cycle.
- **If Render restarted:** broker is the source of truth — on wake the worker reconciles positions vs Alpaca before any new entries (duplicate-proof `client_order_id`s make this safe by construction).
- **If MCP subprocess dies:** supervisor restarts it; executor routes via API meanwhile; alert event visible in journal.
- **If LLM provider errors:** failover chain (Gemini → GPT-4o → Featherless → deterministic fallback); journal notes which model answered each call.
- **Kill switch:** setting `DESK_PAUSED=true` (Render env) stops entries (exits still run) — expected to remain unused.

## 6. Local development

```bash
# worker
cp .env.example .env && fill keys
pip install -r requirements.txt
uvicorn stonks.api:app --reload

# web
cd apps/web && pnpm install
echo 'NEXT_PUBLIC_DESK_URL=http://localhost:8000' > .env.local
pnpm dev
```

Test mode (`STONKS_TEST=true`): deterministic LLM fixtures, dry-run order routing — the full pipeline runs with zero network keys.

## 7. Cost summary

| Item | Cost |
|---|---|
| Vercel hobby | $0 |
| Render free | $0 |
| UptimeRobot free | $0 |
| Gemini Flash (analysts) | ~$0 (free tier) |
| GPT-4o (judge/Sage, ~2 calls/cycle) | ~$1–3 total |
| Featherless | $25 hackathon credits |
| **Total** | **≈ $0–3** |
