const configuredBase = import.meta.env.VITE_API_BASE;
const API_BASE = (configuredBase || window.location.origin).replace(/\/+$/, "");

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || "Request failed");
  }
  return body;
}

export async function createGame(payload) {
  return request("/games", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function joinGame(payload) {
  return request("/games/join", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getGame(gameId) {
  return request(`/games/${gameId}`);
}

export async function getGameByCode(code) {
  return request(`/games/code/${code}`);
}

export async function startGame(gameId, ownerPlayerId) {
  return request(`/games/${gameId}/start`, {
    method: "POST",
    body: JSON.stringify({ owner_player_id: ownerPlayerId }),
  });
}

export async function submitTrade(gameId, payload) {
  return request(`/games/${gameId}/trades`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function markDone(gameId, playerId) {
  return request(`/games/${gameId}/done`, {
    method: "POST",
    body: JSON.stringify({ player_id: playerId }),
  });
}
