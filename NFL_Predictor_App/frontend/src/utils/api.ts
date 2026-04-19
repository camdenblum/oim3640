import axios from 'axios';

export const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('nfl_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res.data,
  (err) => Promise.reject(err.response?.data?.error || err.message)
);

export const endpoints = {
  teams: {
    all: (season?: number) => api.get('/teams', { params: { season } }),
    byId: (id: number) => api.get(`/teams/${id}`),
    stats: (id: number, season?: number) => api.get(`/teams/${id}/stats`, { params: { season } }),
    weeklyStats: (id: number, season?: number) => api.get(`/teams/${id}/stats/weekly`, { params: { season } }),
    roster: (id: number) => api.get(`/teams/${id}/roster`),
    schedule: (id: number, season?: number) => api.get(`/teams/${id}/schedule`, { params: { season } }),
    splits: (id: number) => api.get(`/teams/${id}/splits`),
    situational: (id: number) => api.get(`/teams/${id}/situational`),
    advanced: (id: number) => api.get(`/teams/${id}/advanced`),
    injuries: (id: number) => api.get(`/teams/${id}/injuries`),
    compare: (ids: number[]) => api.get('/teams/compare', { params: { ids: ids.join(',') } }),
  },
  players: {
    all: (params?: object) => api.get('/players', { params }),
    search: (q: string) => api.get('/players/search', { params: { q } }),
    leaderboards: (params?: object) => api.get('/players/leaderboards', { params }),
    byId: (id: number) => api.get(`/players/${id}`),
    stats: (id: number, season?: number) => api.get(`/players/${id}/stats`, { params: { season } }),
    gameLog: (id: number, season?: number) => api.get(`/players/${id}/game-log`, { params: { season } }),
    trends: (id: number) => api.get(`/players/${id}/trends`),
    splits: (id: number) => api.get(`/players/${id}/splits`),
    advanced: (id: number) => api.get(`/players/${id}/advanced`),
    snapCounts: (id: number) => api.get(`/players/${id}/snap-counts`),
    matchupHistory: (id: number, opponentId?: number) =>
      api.get(`/players/${id}/matchup-history`, { params: { opponentId } }),
  },
  games: {
    all: (params?: object) => api.get('/games', { params }),
    upcoming: () => api.get('/games/upcoming'),
    live: () => api.get('/games/live'),
    byId: (id: number) => api.get(`/games/${id}`),
    boxScore: (id: number) => api.get(`/games/${id}/box-score`),
    playByPlay: (id: number) => api.get(`/games/${id}/play-by-play`),
    drives: (id: number) => api.get(`/games/${id}/drives`),
  },
  predictions: {
    games: (week?: number) => api.get('/predictions/games', { params: { week } }),
    gameById: (gameId: number) => api.get(`/predictions/games/${gameId}`),
    gamePlayers: (gameId: number) => api.get(`/predictions/games/${gameId}/players`),
    player: (playerId: number) => api.get(`/predictions/players/${playerId}`),
    season: (teamId: number) => api.get(`/predictions/season/${teamId}`),
    playoffs: () => api.get('/predictions/playoffs'),
    simulate: (body: object) => api.post('/predictions/simulate', body),
    accuracy: () => api.get('/predictions/accuracy'),
    leaderboard: (week?: number) => api.get('/predictions/leaderboard', { params: { week } }),
  },
  analytics: {
    standings: (season?: number) => api.get('/analytics/standings', { params: { season } }),
    powerRankings: (week?: number, season?: number) =>
      api.get('/analytics/power-rankings', { params: { week, season } }),
    scheduleDifficulty: () => api.get('/analytics/schedule-difficulty'),
    trends: (season?: number) => api.get('/analytics/trends', { params: { season } }),
    matchups: (gameId: number) => api.get(`/analytics/matchups/${gameId}`),
    weather: (week?: number) => api.get('/analytics/weather', { params: { week } }),
  },
};
