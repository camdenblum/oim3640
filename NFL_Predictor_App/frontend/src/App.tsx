import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import TeamsPage from './pages/TeamsPage';
import TeamDetailPage from './pages/TeamDetailPage';
import PlayersPage from './pages/PlayersPage';
import PlayerProfilePage from './pages/PlayerProfilePage';
import GamesPage from './pages/GamesPage';
import GameDetailPage from './pages/GameDetailPage';
import PredictionsPage from './pages/PredictionsPage';
import GamePredictionPage from './pages/GamePredictionPage';
import PlayerProjectionsPage from './pages/PlayerProjectionsPage';
import SeasonProjectionsPage from './pages/SeasonProjectionsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import PowerRankingsPage from './pages/PowerRankingsPage';
import ModelPage from './pages/ModelPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="teams" element={<TeamsPage />} />
          <Route path="teams/:id" element={<TeamDetailPage />} />
          <Route path="players" element={<PlayersPage />} />
          <Route path="players/:id" element={<PlayerProfilePage />} />
          <Route path="games" element={<GamesPage />} />
          <Route path="games/:id" element={<GameDetailPage />} />
          <Route path="predict" element={<PredictionsPage />} />
          <Route path="predict/game/:id" element={<GamePredictionPage />} />
          <Route path="predict/players" element={<PlayerProjectionsPage />} />
          <Route path="predict/season" element={<SeasonProjectionsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="analytics/power-rankings" element={<PowerRankingsPage />} />
          <Route path="model" element={<ModelPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
