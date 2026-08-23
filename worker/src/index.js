import { livePayload, normalizeFixture } from "./normalize.js";

const API_BASE = "https://v3.football.api-sports.io";
const CACHE_SECONDS = 60;

function corsHeaders(request, env) {
  const origin = request.headers.get("Origin") || "";
  const allowed = String(env.ALLOWED_ORIGINS || "").split(",").map(value => value.trim());
  return {
    "Access-Control-Allow-Origin": allowed.includes(origin) ? origin : allowed[0] || "https://kickdex.alvarocarpintero.com",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function json(request, env, body, status = 200, cache = "no-store") {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": cache,
      ...corsHeaders(request, env),
    },
  });
}

async function providerFetch(path, env) {
  if (!env.LIVE_API_KEY) throw new Error("LIVE_API_KEY is not configured");
  const response = await fetch(API_BASE + path, {
    headers: { "x-apisports-key": env.LIVE_API_KEY },
  });
  if (!response.ok) throw new Error("provider HTTP " + response.status);
  const payload = await response.json();
  const providerError = payload.errors && Object.keys(payload.errors).length ? JSON.stringify(payload.errors) : null;
  if (providerError) throw new Error(providerError);
  return payload.response || [];
}

async function withCache(request, env, key, loader) {
  const cache = caches.default;
  const cacheRequest = new Request(new URL(key, request.url), { method: "GET" });
  const hit = await cache.match(cacheRequest);
  if (hit) return hit;
  try {
    const body = await loader();
    const response = json(request, env, body, 200, "public, max-age=15, s-maxage=" + CACHE_SECONDS);
    await cache.put(cacheRequest, response.clone());
    if (env.LIVE_CACHE) await env.LIVE_CACHE.put(key, JSON.stringify(body), { expirationTtl: 86400 });
    return response;
  } catch (error) {
    const saved = env.LIVE_CACHE ? await env.LIVE_CACHE.get(key, "json") : null;
    if (saved) return json(request, env, { ...saved, stale: true, error: String(error.message || error) });
    return json(request, env, livePayload([], { stale: true, error: String(error.message || error) }), 502);
  }
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders(request, env) });
    if (request.method !== "GET") return json(request, env, { error: "method_not_allowed" }, 405);

    const url = new URL(request.url);
    if (url.pathname === "/v1/health") {
      return json(request, env, {
        ok: true,
        enabled: env.LIVE_API_ENABLED === "true",
        provider: env.LIVE_PROVIDER || null,
      });
    }

    if (env.LIVE_API_ENABLED !== "true") {
      return json(request, env, livePayload([], { enabled: false, stale: true, error: "live_feed_disabled" }));
    }

    if (url.pathname === "/v1/live") {
      const leagues = (url.searchParams.get("leagues") || "all").replace(/[^0-9-]/g, "");
      const path = "/fixtures?live=" + (leagues || "all");
      return withCache(request, env, "/cache/live/" + (leagues || "all"), async () => livePayload(await providerFetch(path, env)));
    }

    const match = url.pathname.match(/^\/v1\/matches\/(\d+)$/);
    if (match) {
      return withCache(request, env, "/cache/matches/" + match[1], async () => {
        const items = await providerFetch("/fixtures?id=" + match[1]);
        return {
          enabled: true,
          updated_at: new Date().toISOString(),
          stale: false,
          source: "api-football",
          match: items[0] ? normalizeFixture(items[0]) : null,
        };
      });
    }

    return json(request, env, { error: "not_found" }, 404);
  },
};
