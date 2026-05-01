'use client';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

type Phase = 'inhale' | 'hold' | 'exhale' | 'done';

const PHASES: { phase: Phase; label: string; duration: number }[] = [
  { phase: 'inhale',  label: 'Breathe in...',  duration: 4 },
  { phase: 'hold',    label: 'Hold...',         duration: 7 },
  { phase: 'exhale',  label: 'Breathe out...', duration: 8 },
];

const CYCLE_TOTAL = PHASES.reduce((s, p) => s + p.duration, 0);

const PHASE_COLORS: Record<Phase, string> = {
  inhale: '#4a7a23',
  hold:   '#C4870A',
  exhale: '#6B94A8',
  done:   '#2D5016',
};

const PHASE_SCALE: Record<Phase, number> = {
  inhale: 1.4,
  hold:   1.4,
  exhale: 1.0,
  done:   1.0,
};

interface Props {
  onComplete?: () => void;
}

export default function BreathingExercise({ onComplete }: Props) {
  const [currentPhaseIdx, setCurrentPhaseIdx] = useState(0);
  const [secondsLeft, setSecondsLeft] = useState(PHASES[0].duration);
  const [started, setStarted] = useState(false);
  const [cyclesLeft, setCyclesLeft] = useState(2);
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    if (!started || finished) return;

    const interval = setInterval(() => {
      setSecondsLeft((s) => {
        if (s > 1) return s - 1;

        const nextIdx = (currentPhaseIdx + 1) % PHASES.length;
        if (nextIdx === 0) {
          const remaining = cyclesLeft - 1;
          if (remaining <= 0) {
            clearInterval(interval);
            setFinished(true);
            onComplete?.();
            return 0;
          }
          setCyclesLeft(remaining);
        }
        setCurrentPhaseIdx(nextIdx);
        return PHASES[nextIdx].duration;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [started, currentPhaseIdx, cyclesLeft, finished, onComplete]);

  const phase = PHASES[currentPhaseIdx];
  const color = PHASE_COLORS[finished ? 'done' : phase.phase];

  if (!started) {
    return (
      <div className="text-center">
        <div className="w-32 h-32 rounded-full bg-forest/10 mx-auto flex items-center justify-center mb-6">
          <span className="text-5xl">🌬️</span>
        </div>
        <button onClick={() => setStarted(true)} className="btn-primary">
          Start breathing exercise
        </button>
      </div>
    );
  }

  if (finished) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center"
      >
        <motion.div
          className="w-32 h-32 rounded-full mx-auto flex items-center justify-center mb-4"
          style={{ backgroundColor: `${color}22`, border: `3px solid ${color}` }}
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 1.5, repeat: 1 }}
        >
          <span className="text-5xl">🌿</span>
        </motion.div>
        <p className="font-serif text-lg text-forest">Well done. Take a moment.</p>
      </motion.div>
    );
  }

  return (
    <div className="flex flex-col items-center">
      <motion.div
        className="w-32 h-32 rounded-full flex items-center justify-center mb-6 relative"
        style={{ backgroundColor: `${color}22`, border: `3px solid ${color}` }}
        animate={{ scale: PHASE_SCALE[phase.phase] }}
        transition={{ duration: phase.duration, ease: phase.phase === 'inhale' ? 'easeIn' : phase.phase === 'exhale' ? 'easeOut' : 'linear' }}
      >
        <span className="font-serif text-3xl font-semibold" style={{ color }}>{secondsLeft}</span>
      </motion.div>

      <AnimatePresence mode="wait">
        <motion.p
          key={phase.phase}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          className="font-serif text-lg text-forest mb-2"
        >
          {phase.label}
        </motion.p>
      </AnimatePresence>
      <p className="text-earth/40 text-xs">{cyclesLeft} cycle{cyclesLeft !== 1 ? 's' : ''} remaining</p>
    </div>
  );
}
