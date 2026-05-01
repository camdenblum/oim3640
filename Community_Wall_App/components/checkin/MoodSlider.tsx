'use client';

const MOOD_EMOJIS = ['😔', '😕', '😐', '🙂', '😊'];

interface Props {
  value: number;
  onChange: (v: number) => void;
}

export default function MoodSlider({ value, onChange }: Props) {
  return (
    <div>
      <div className="flex justify-between mb-3">
        {MOOD_EMOJIS.map((emoji, i) => (
          <button
            key={i}
            onClick={() => onChange(i + 1)}
            aria-label={`Mood level ${i + 1}`}
            aria-pressed={value === i + 1}
            className={`text-3xl transition-all duration-200 ${
              value === i + 1
                ? 'scale-125 filter-none'
                : 'opacity-30 hover:opacity-60 hover:scale-110'
            }`}
          >
            {emoji}
          </button>
        ))}
      </div>
      <input
        type="range"
        min={1}
        max={5}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 rounded-full appearance-none cursor-pointer"
        style={{
          background: `linear-gradient(to right, #2D5016 ${(value - 1) * 25}%, #EDE8DC ${(value - 1) * 25}%)`,
        }}
        aria-label="Mood slider"
        aria-valuemin={1}
        aria-valuemax={5}
        aria-valuenow={value}
      />
    </div>
  );
}
