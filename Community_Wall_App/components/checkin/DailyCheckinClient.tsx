'use client';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MoodSlider from './MoodSlider';
import BreathingExercise from './BreathingExercise';
import MoodGraph from '../profile/MoodGraph';

const MOOD_LABELS = ['Really struggling', 'A bit rough', 'Okay', 'Pretty good', 'Doing great'];
const MOOD_PROMPTS = [
  "What's one thing on your mind today?",
  "What's one thing that felt heavy today?",
  "What's one thing that felt okay today?",
  "What's one thing you're grateful for?",
  "What made today good?",
];

interface CheckinHistory {
  check_in_date: string;
  mood_score: number;
}

interface Props {
  alreadyCheckedIn: boolean;
  existingCheckin: { mood_score: number; journal_text?: string | null } | null;
  history: CheckinHistory[];
}

type Step = 'mood' | 'journal' | 'breathing' | 'done';

export default function DailyCheckinClient({ alreadyCheckedIn, existingCheckin, history }: Props) {
  const [step, setStep] = useState<Step>(alreadyCheckedIn ? 'done' : 'mood');
  const [mood, setMood] = useState(alreadyCheckedIn ? existingCheckin?.mood_score ?? 3 : 3);
  const [journal, setJournal] = useState('');
  const [breathingDone, setBreathingDone] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  async function submitCheckin(skipBreathing = false) {
    setSubmitting(true);
    setError('');

    const res = await fetch('/api/checkin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mood_score: mood,
        journal_text: journal.trim() || null,
        completed_breathing: skipBreathing ? false : breathingDone,
      }),
    });

    setSubmitting(false);
    const data = await res.json();
    if (!res.ok && res.status !== 409) {
      setError(data.error ?? 'Something went wrong');
      return;
    }
    setStep('done');
  }

  return (
    <div className="space-y-6">
      <AnimatePresence mode="wait">
        {step === 'mood' && (
          <motion.div
            key="mood"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="card-surface"
          >
            <h2 className="font-serif text-xl text-forest mb-2">How are you feeling today?</h2>
            <p className="text-earth/60 text-sm mb-8">Be honest. This is just for you.</p>
            <MoodSlider value={mood} onChange={setMood} />
            <p className="text-center mt-4 text-forest font-semibold">{MOOD_LABELS[mood - 1]}</p>
            <button
              onClick={() => setStep('journal')}
              className="btn-primary w-full mt-8"
            >
              Continue →
            </button>
          </motion.div>
        )}

        {step === 'journal' && (
          <motion.div
            key="journal"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="card-surface"
          >
            <h2 className="font-serif text-xl text-forest mb-2">One quick thought</h2>
            <p className="text-earth/60 text-sm mb-5 italic">{MOOD_PROMPTS[mood - 1]}</p>
            <textarea
              value={journal}
              onChange={(e) => setJournal(e.target.value.slice(0, 280))}
              placeholder="Optional — just for you, never shared."
              rows={4}
              className="form-input resize-none font-serif mb-1"
              aria-label="Private journal prompt"
            />
            <p className="text-right text-xs text-earth/30 mb-6">{journal.length}/280</p>
            <div className="flex gap-3">
              <button onClick={() => setStep('breathing')} className="btn-primary flex-1">
                Take a breath →
              </button>
              <button onClick={() => submitCheckin(true)} disabled={submitting} className="btn-ghost text-sm">
                Skip & finish
              </button>
            </div>
          </motion.div>
        )}

        {step === 'breathing' && (
          <motion.div
            key="breathing"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="card-surface text-center"
          >
            <h2 className="font-serif text-xl text-forest mb-2">One breath together</h2>
            <p className="text-earth/60 text-sm mb-8">4 seconds in · 7 hold · 8 out</p>
            <BreathingExercise onComplete={() => setBreathingDone(true)} />
            {error && <p className="text-red-600 text-sm mt-4" role="alert">{error}</p>}
            <button
              onClick={() => submitCheckin()}
              disabled={submitting}
              className="btn-primary mt-8 w-full"
            >
              {submitting ? 'Saving...' : 'Finish check-in +25 HP'}
            </button>
          </motion.div>
        )}

        {step === 'done' && (
          <motion.div
            key="done"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card-surface text-center"
          >
            <p className="text-5xl mb-4">🌿</p>
            <h2 className="font-serif text-2xl text-forest mb-2">
              {alreadyCheckedIn && !breathingDone
                ? "You've already checked in today."
                : "Check-in complete."}
            </h2>
            <p className="text-earth/70 mb-2">
              {alreadyCheckedIn && !breathingDone
                ? "Come back tomorrow. You showed up — that counts."
                : "You showed up for yourself today. That matters."}
            </p>
            {!alreadyCheckedIn && (
              <p className="text-amber font-semibold text-sm">+25 Healing Points earned</p>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mood history */}
      {history.length > 1 && (
        <div className="card-surface">
          <h3 className="font-serif text-lg text-forest mb-4">Your mood over time</h3>
          <p className="text-earth/50 text-xs mb-4">Private — only visible to you</p>
          <MoodGraph history={history} />
        </div>
      )}
    </div>
  );
}
