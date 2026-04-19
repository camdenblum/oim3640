import { SHORTCUTS } from '../hooks/useKeyboardShortcuts';

/** Hidden by default — toggle with the '?' key. */
export default function KeyboardHelp() {
  return (
    <div id="kbd-help" className="hidden fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={() => document.getElementById('kbd-help')?.classList.add('hidden')}>
      <div className="bg-nfl-card border border-nfl-border rounded-xl p-6 w-80 shadow-2xl"
        onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-lg">Keyboard Shortcuts</h2>
          <button
            className="text-gray-500 hover:text-white text-lg leading-none"
            onClick={() => document.getElementById('kbd-help')?.classList.add('hidden')}>
            ✕
          </button>
        </div>
        <div className="space-y-2">
          {SHORTCUTS.map(({ key, desc }) => (
            <div key={key} className="flex items-center justify-between text-sm">
              <span className="text-gray-400">{desc}</span>
              <kbd className="bg-gray-800 border border-gray-600 rounded px-2 py-0.5 font-mono text-xs text-gray-200">
                {key}
              </kbd>
            </div>
          ))}
        </div>
        <p className="mt-4 text-xs text-gray-500 text-center">Press <kbd className="bg-gray-800 border border-gray-600 rounded px-1 font-mono">?</kbd> or click outside to close</p>
      </div>
    </div>
  );
}
