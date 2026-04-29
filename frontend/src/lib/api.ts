const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchTeams() {
  const res = await fetch(`${API_BASE_URL}/teams`);
  if (!res.ok) throw new Error('Failed to fetch teams');
  return res.json();
}

export async function fetchTeamMatches(teamName: string) {
  const res = await fetch(`${API_BASE_URL}/matches/${encodeURIComponent(teamName)}`);
  if (!res.ok) throw new Error('Failed to fetch matches');
  return res.json();
}
