import test from "node:test";
import assert from "node:assert/strict";

import { livePayload, normalizeFixture } from "../src/normalize.js";

test("normalizes a live fixture into the public contract", () => {
  const value = normalizeFixture({
    fixture: { id: 7, date: "2026-08-23T20:00:00Z", status: { short: "2H", long: "Second Half", elapsed: 63 } },
    league: { id: 140, name: "La Liga", country: "Spain" },
    teams: { home: { id: 1, name: "Home", logo: "home.png" }, away: { id: 2, name: "Away", logo: "away.png" } },
    goals: { home: 2, away: 1 },
  });

  assert.equal(value.id, "7");
  assert.equal(value.status, "2H");
  assert.equal(value.minute, 63);
  assert.deepEqual(value.score, { home: 2, away: 1 });
});

test("disabled payload is explicit and empty", () => {
  const value = livePayload([], { enabled: false, stale: true, error: "live_feed_disabled" });
  assert.equal(value.enabled, false);
  assert.equal(value.stale, true);
  assert.deepEqual(value.matches, []);
});
