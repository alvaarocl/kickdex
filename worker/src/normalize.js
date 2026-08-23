export function normalizeFixture(item = {}) {
  const fixture = item.fixture || {};
  const league = item.league || {};
  const teams = item.teams || {};
  const goals = item.goals || {};
  const status = fixture.status || {};
  return {
    id: String(fixture.id || ""),
    league: {
      id: league.id ?? null,
      name: league.name || "",
      country: league.country || "",
      logo: league.logo || null,
    },
    kickoff: fixture.date || null,
    status: status.short || "NS",
    status_label: status.long || "",
    minute: status.elapsed ?? null,
    extra_minute: status.extra ?? null,
    referee: fixture.referee || null,
    venue: fixture.venue?.name || null,
    home: {
      id: teams.home?.id ?? null,
      name: teams.home?.name || "",
      crest: teams.home?.logo || null,
      winner: teams.home?.winner ?? null,
    },
    away: {
      id: teams.away?.id ?? null,
      name: teams.away?.name || "",
      crest: teams.away?.logo || null,
      winner: teams.away?.winner ?? null,
    },
    score: {
      home: goals.home ?? null,
      away: goals.away ?? null,
    },
    events: normalizeEvents(item.events || []),
    statistics: item.statistics || [],
    lineups: item.lineups || [],
  };
}

export function normalizeEvents(events) {
  return events.map(event => ({
    minute: event.time?.elapsed ?? null,
    extra_minute: event.time?.extra ?? null,
    team_id: event.team?.id ?? null,
    team: event.team?.name || "",
    player_id: event.player?.id ?? null,
    player: event.player?.name || "",
    assist_id: event.assist?.id ?? null,
    assist: event.assist?.name || "",
    type: event.type || "",
    detail: event.detail || "",
    comments: event.comments || null,
  }));
}

export function livePayload(items, { stale = false, enabled = true, error = null } = {}) {
  return {
    enabled,
    updated_at: new Date().toISOString(),
    stale,
    source: enabled ? "api-football" : null,
    error,
    matches: items.map(normalizeFixture),
  };
}
