# KICKDEX live worker

Provider-agnostic public contract for the future live match centre.

- Production defaults to `LIVE_API_ENABLED=false`.
- Store the provider key with `wrangler secret put LIVE_API_KEY`; never add it to `wrangler.jsonc`.
- Optional KV binding `LIVE_CACHE` preserves the last successful payload for stale fallback.
- Endpoints: `GET /v1/health`, `GET /v1/live?leagues=140-39`, and `GET /v1/matches/:id`.

Do not enable the worker until the selected provider grants access to season 2026/27.
