# AGENTS.md

The shared operating guide for any coding agent working on KICKDEX (Claude Code, Codex, Cursor, Aider, etc.) lives in [`CLAUDE.md`](CLAUDE.md) — it is the **single source of truth** for product direction, brand voice, stack decisions, sprint plan, testing expectations, and legal guardrails. Read it before editing.

Project notes, data contracts and the historical PRD/plans live in [`docs_proyecto/`](docs_proyecto/).

If your tooling reads `AGENTS.md` by convention (Codex CLI, OpenHands, etc.), this file is just a pointer — everything you need is in the files above.

## TL;DR

- Static-first: `docs/` is the public product. No new public backends without approval.
- Brand V3 voice: CLI-style English brand phrases (`> launch terminal_`, `> RISK NOTICE`, tagline) stay English in both locales. Everything else uses the i18n system.
- Honest copy: never overstate coverage. If a feature has partial data, say so in the UI.
- Run tests before declaring done. See `CLAUDE.md` → Testing Expectations.
- When in doubt about scope, legal data, API keys, or stack decisions, ask the human.
