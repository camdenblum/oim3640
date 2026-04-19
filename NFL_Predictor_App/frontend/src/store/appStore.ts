import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AppStore {
  currentWeek: number;
  currentSeason: number;
  darkMode: boolean;
  user: { id: number; email: string; name: string; role: string } | null;
  token: string | null;
  setWeek: (week: number) => void;
  setSeason: (season: number) => void;
  toggleDarkMode: () => void;
  setUser: (user: AppStore['user'], token: string) => void;
  logout: () => void;
}

function getCurrentNFLSeason() {
  const now = new Date();
  return now.getMonth() >= 8 ? now.getFullYear() : now.getFullYear() - 1;
}

function getCurrentNFLWeek() {
  const now = new Date();
  const seasonStart = new Date(now.getFullYear(), 8, 5);
  if (now < seasonStart) return 1;
  const diff = Math.floor((now.getTime() - seasonStart.getTime()) / (7 * 24 * 60 * 60 * 1000));
  return Math.min(Math.max(diff + 1, 1), 18);
}

export const useAppStore = create<AppStore>()(
  persist(
    (set) => ({
      currentWeek: getCurrentNFLWeek(),
      currentSeason: getCurrentNFLSeason(),
      darkMode: true,
      user: null,
      token: null,
      setWeek: (week) => set({ currentWeek: Math.min(Math.max(week, 1), 22) }),
      setSeason: (season) => set({ currentSeason: season }),
      toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),
      setUser: (user, token) => {
        localStorage.setItem('nfl_token', token);
        set({ user, token });
      },
      logout: () => {
        localStorage.removeItem('nfl_token');
        set({ user: null, token: null });
      },
    }),
    { name: 'nfl-predictor-store', partialize: (s) => ({ darkMode: s.darkMode, currentWeek: s.currentWeek }) }
  )
);
