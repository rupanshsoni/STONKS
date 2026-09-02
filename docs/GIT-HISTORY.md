# GIT HISTORY — Commit Plan & Annotated Log

> Accurately maintained and documented history: conventional commits, one logical change each, mapped 1:1 to milestones. This file is the annotated companion to `git log` — what each commit delivered and why, in order.

## 1. Conventions

- **Format:** Conventional Commits — `type(scope): summary` · types: `feat docs fix test chore build ci refactor` · scopes: `web desk kernel alpaca agents memory brand repo`.
- **Rules:** one logical change per commit; body explains *why* when non-obvious; no fixup-squash churn (small, real commits tell a better story than one mega-push — judges check repo activity across the event window).
- **Tags:** `v0.1.0-mvp` at first deployable end-to-end cycle; `v1.0.0-submission` at submission freeze.
- **Branches:** `main` (always deployable) + short-lived feature branches for anything risky (`feat/mascots`, `feat/sage`), merged with `--no-ff` to keep milestone boundaries visible.

## 2. The plan (execution order ≈ commit order)

| # | Commit | Delivers |
|---|---|---|
| 1 | `chore(repo): init — license, gitignore` | MIT LICENSE, .gitignore (paper-secrets hygiene from line one) |
| 2 | `docs(repo): readme + planning pack — mvp, architecture, agents, ui, brand, alpaca, risk, git-history, deployment, submission` | full README, the complete docs set, brand logo |
| 3 | `build(desk): fastapi skeleton, config, env handling` | stonks/ package, health endpoint, paper-mode guard scaffold |
| 4 | `feat(alpaca): client + paper guards + account/clock endpoints` | alpaca-py wiring, guards, account snapshot |
| 5 | `feat(desk): journal + SSE event bus` | append-only JSONL journal; /events SSE |
| 6 | `feat(alpaca): executor — atomic mleg orders, idempotent ids` | order placement incl. negative-credit convention |
| 7 | `feat(kernel): the 12 gates + sizing + exit ladder` | risk kernel with reason codes |
| 8 | `feat(agents): code analysts (trend, IVR, GEX, liquidity, events)` | deterministic analyst layer |
| 9 | `feat(agents): senti — sentiment analyst (gemini) with citations` | sentiment spec implementation |
| 10 | `feat(agents): debate — toro/ursa rounds + verdi verdict (gpt-4o)` | debate protocol + judge |
| 11 | `feat(agents): structurer — regime router + structure menu` | code-picked strikes/wings/DTE |
| 12 | `feat(alpaca): mcp integration — official server subprocess + tool loop` | MCP surface + supervisor |
| 13 | `feat(alpaca): cli reconciliation + dry-run tests` | independent source of truth |
| 14 | `feat(desk): cycle orchestrator — full pipeline loop` | the tick() scheduler wiring everything |
| 15 | `build(web): next.js scaffold + tokens + shell` | app dir, tailwind tokens from logo, sidebar/topbar |
| 16 | `feat(web): live overview — kpi strip, equity curve, feed` | SSE consumption, decision cards |
| 17 | `feat(web): positions + journal pages` | tables, filters, receipts |
| 18 | `feat(mascots): shared facet anatomy + state timelines` | MascotAvatar, GSAP states, cast config |
| 19 | `feat(web): cast integration — dock, feed avatars, glitch signature` | the 8 characters live |
| 20 | `feat(memory): L1/L2/L3 layers + persistence` | snapshots, ledger, lessons |
| 21 | `feat(agents): sage — post-mortem + restrict-only param proposals` | self-improvement loop |
| 22 | `feat(web): /memory + /risk pages` | lessons timeline, gate wall |
| 23 | `feat(desk): /ask copilot — user-prompted analysis queue` | natural-language requests → pipeline |
| 24 | `feat(web): /ask page + copilot UX` | request → verdict flow incl. honest rejections |
| 25 | `test(kernel): gate property tests + guard/idempotency/reconcile tests` | the 50+ test suite |
| 26 | `fix(desk): hardening pass — rate limits, cache, failover chain` | LLM failover, retries |
| 27 | `build(repo): render + vercel deploy configs` | render.yaml, vercel settings, cron ping |
| 28 | `docs(repo): README final — architecture diagram, screenshots, quickstart` | the repo face |
| 29 | `docs(repo): submission pack — video script, one-pager, slides content` | SUBMISSION.md completion |
| 30 | `chore(repo): v1.0.0-submission freeze` | tag + final housekeeping |

## 3. Annotated log (running — updated at each tag)

### v0.1.0-mvp (first end-to-end cycle)
*(filled when tagged — expected after commit 14)*

- Commits 1–2: project foundations — license, planning docs written before code (docs-first is deliberate: the plan *is* the product).
- Commits 3–7: the desk's spine — API skeleton → Alpaca client (paper-guarded from the first line) → journal/SSE (observability before intelligence) → executor → risk kernel (safety before strategy).
- Commits 8–14: the brain — analysts → sentiment → debate → structurer → MCP/CLI surfaces → orchestrator closes the loop. *The account is live and trading from commit 6 onward.*

### v1.0.0-submission (freeze)
*(filled at submission — commits 15–30: the face, the cast, memory & Sage, copilot, tests, deploy, docs.)*

## 4. What the history is designed to demonstrate

1. **Docs-first discipline** — the planning pack precedes code.
2. **Safety-first sequencing** — journal, guards, and kernel land *before* any agent can trade.
3. **Continuous activity across the event window** — small real commits, not one final dump.
4. **Milestone legibility** — a judge reading `git log` + this file can reconstruct the entire build in two minutes.

## 5. Hygiene rules

- `.gitignore` excludes: `.env*`, `*.db`, `*.sqlite*`, `node_modules/`, `.next/`, `__pycache__/`, `dist/`, `docs/~$*` (Word lock files), `.agents/` (local skills), `skills-lock.json`, and the *strategic* research docs (`docs/0[1-8]-*.md` + `*.docx` — internal recon; the repo carries only STONKS' own docs).
- Assets: `Assets/logo.png` stays at repo root (README-relative path) *and* ships to `apps/web/public/brand/logo.png` for the app.
- No secrets ever: pre-commit secret scan; keys only via env vars.
- No force-pushes on `main`; history is the artifact.
