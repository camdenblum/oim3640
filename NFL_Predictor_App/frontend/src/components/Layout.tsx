import { Outlet, NavLink, Link } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import KeyboardHelp from './KeyboardHelp';

export default function Layout() {
  const { darkMode, toggleDarkMode, user, logout } = useAppStore();
  useKeyboardShortcuts();

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="min-h-screen bg-nfl-dark text-white">
        <nav className="sticky top-0 z-50 bg-nfl-card/95 backdrop-blur border-b border-nfl-border">
          <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 gradient-nfl rounded-lg flex items-center justify-center font-bold text-sm">NFL</div>
              <span className="font-bold text-lg hidden sm:block">Predictor</span>
            </Link>
            <div className="flex items-center gap-1 text-sm">
              {[
                { to: '/teams', label: 'Teams' },
                { to: '/players', label: 'Players' },
                { to: '/games', label: 'Games' },
                { to: '/predict', label: 'Predict' },
                { to: '/analytics', label: 'Analytics' },
                { to: '/model', label: 'Model' },
              ].map(({ to, label }) => (
                <NavLink key={to} to={to}
                  className={({ isActive }) =>
                    `px-3 py-1.5 rounded-lg transition-colors ${isActive ? 'bg-nfl-blue text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`
                  }>
                  {label}
                </NavLink>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <button
                title="Keyboard shortcuts (?)"
                onClick={() => document.getElementById('kbd-help')?.classList.toggle('hidden')}
                className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-800 text-gray-400 text-xs font-bold border border-gray-700">
                ?
              </button>
              <button onClick={toggleDarkMode}
                className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-800 text-gray-400">
                {darkMode ? '☀️' : '🌙'}
              </button>
              {user ? (
                <button onClick={logout} className="text-xs text-gray-400 hover:text-white">Logout</button>
              ) : (
                <Link to="/login" className="text-xs btn-primary">Login</Link>
              )}
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 py-6">
          <Outlet />
        </main>
        <footer className="border-t border-nfl-border mt-16 py-6 text-center text-xs text-gray-500">
          NFL Predictor — Data sourced from ESPN Public API &amp; NFLverse. For educational/research purposes only.
          <span className="ml-3 opacity-50">Press <kbd className="font-mono bg-gray-800 border border-gray-700 rounded px-1">?</kbd> for shortcuts</span>
        </footer>
      </div>
      <KeyboardHelp />
    </div>
  );
}
