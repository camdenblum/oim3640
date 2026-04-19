import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/appStore';

/**
 * Global keyboard shortcuts:
 *   G  → /games
 *   T  → /teams
 *   P  → /players
 *   R  → /predict   (pRedict)
 *   A  → /analytics
 *   M  → /model
 *   /  → focus search (if page exposes one via data-shortcut-search)
 *   ?  → toggle shortcut help overlay
 *
 * N / Shift+N → next / previous week on any page that exposes
 *   a [data-shortcut-week] input (set by the week selector).
 *
 * Shortcuts are suppressed when focus is inside an input/textarea/select.
 */
export function useKeyboardShortcuts() {
  const navigate = useNavigate();
  const { currentWeek, setWeek } = useAppStore();

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (['input', 'textarea', 'select'].includes(tag)) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;

      switch (e.key) {
        case 'g': navigate('/games'); break;
        case 't': navigate('/teams'); break;
        case 'p': navigate('/players'); break;
        case 'r': navigate('/predict'); break;
        case 'a': navigate('/analytics'); break;
        case 'm': navigate('/model'); break;

        case 'n':
          if (e.shiftKey) {
            setWeek(Math.max(1, currentWeek - 1));
          } else {
            setWeek(Math.min(18, currentWeek + 1));
          }
          break;

        case '/': {
          e.preventDefault();
          const searchEl = document.querySelector<HTMLElement>('[data-shortcut-search]');
          searchEl?.focus();
          break;
        }

        case '?': {
          const el = document.getElementById('kbd-help');
          if (el) el.classList.toggle('hidden');
          break;
        }
      }
    }

    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [navigate, currentWeek, setWeek]);
}

/** Shortcut map shown in the help overlay */
export const SHORTCUTS = [
  { key: 'G', desc: 'Games' },
  { key: 'T', desc: 'Teams' },
  { key: 'P', desc: 'Players' },
  { key: 'R', desc: 'Predictions' },
  { key: 'A', desc: 'Analytics' },
  { key: 'M', desc: 'Model' },
  { key: 'N', desc: 'Next week' },
  { key: 'Shift+N', desc: 'Previous week' },
  { key: '/', desc: 'Focus search' },
  { key: '?', desc: 'Toggle this help' },
];
