'use client';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Prompt } from '@/lib/types';
import Link from 'next/link';

const MAX_CHARS = 500;

interface Props {
  prompts: Prompt[];
  userId: string | null;
  respondedPrompts: string[];
  onSubmitted: (newResponse: unknown) => void;
}

export default function SubmitForm({ prompts, userId, respondedPrompts, onSubmitted }: Props) {
  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null);
  const [content, setContent] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [showCrisis, setShowCrisis] = useState(false);
  const [success, setSuccess] = useState(false);

  const availablePrompts = prompts.filter((p) => !respondedPrompts.includes(p.id));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedPrompt || !content.trim() || !userId) return;
    setSubmitting(true);
    setError('');

    const res = await fetch('/api/responses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt_id: selectedPrompt.id,
        content: content.trim(),
        display_name: displayName.trim() || 'a voice from the community',
      }),
    });

    const data = await res.json();
    setSubmitting(false);

    if (data.crisis) {
      setShowCrisis(true);
      return;
    }

    if (!res.ok) {
      setError(data.error ?? 'Something went wrong. Please try again.');
      return;
    }

    setSuccess(true);
    setContent('');
    setSelectedPrompt(null);
    if (data.response) onSubmitted(data.response);
  }

  if (!userId) {
    return (
      <div className="card-surface text-center py-8 mb-8">
        <p className="font-serif text-lg text-forest mb-2">Your voice belongs here.</p>
        <p className="text-earth/70 text-sm mb-4">
          Join to add your card to the wall and earn Healing Points.
        </p>
        <Link href="/auth" className="btn-primary inline-block">Sign in to share →</Link>
      </div>
    );
  }

  if (availablePrompts.length === 0) {
    return (
      <div className="card-surface text-center py-8 mb-8">
        <p className="text-3xl mb-3">🌿</p>
        <p className="font-serif text-lg text-forest mb-2">You&apos;ve answered every prompt this week.</p>
        <p className="text-earth/60 text-sm">Come back next week when new prompts arrive. Thank you for sharing.</p>
      </div>
    );
  }

  if (showCrisis) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-forest/5 border border-forest/20 rounded-2xl p-8 mb-8 text-center"
      >
        <p className="text-3xl mb-4">🤍</p>
        <h3 className="font-serif text-xl text-forest mb-3">We hear you.</h3>
        <p className="text-earth/80 leading-relaxed mb-5 max-w-sm mx-auto">
          It sounds like you might be going through something really hard right now.
          You don&apos;t have to face it alone.
        </p>
        <div className="space-y-2">
          <a href="tel:988" className="btn-primary block">Call or text 988 — free, 24/7</a>
          <a href="sms:741741?body=HOME" className="btn-secondary block">Text HOME to 741741</a>
        </div>
        <p className="text-earth/50 text-xs mt-5">
          Your card has been saved for human review. We care about you.
        </p>
      </motion.div>
    );
  }

  if (success) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-surface text-center py-8 mb-8"
      >
        <p className="text-3xl mb-3">🌿</p>
        <p className="font-serif text-xl text-forest mb-2">Your voice has been added to the wall.</p>
        <p className="text-earth/70 text-sm mb-4">+50 Healing Points earned. Thank you for being here.</p>
        <div className="flex justify-center gap-3">
          <button onClick={() => setSuccess(false)} className="btn-secondary text-sm">
            Add another card
          </button>
          <Link href="/learn" className="btn-ghost text-sm">
            Read something helpful →
          </Link>
        </div>
      </motion.div>
    );
  }

  return (
    <div className="card-surface mb-8">
      <h2 className="font-serif text-xl text-forest mb-1">Add your card</h2>
      <p className="text-earth/60 text-sm mb-5">
        Your words might be the ones someone needs to read tonight.
      </p>

      {/* Prompt selection */}
      <div className="space-y-2 mb-5">
        {availablePrompts.map((p) => (
          <button
            key={p.id}
            onClick={() => setSelectedPrompt(selectedPrompt?.id === p.id ? null : p)}
            className={`w-full text-left px-4 py-3 rounded-xl border text-sm transition-all ${
              selectedPrompt?.id === p.id
                ? 'border-forest/40 bg-forest/5 text-forest font-medium'
                : 'border-earth/15 hover:border-forest/20 hover:bg-forest/5 text-earth/80'
            }`}
          >
            {p.text}
          </button>
        ))}
      </div>

      <AnimatePresence>
        {selectedPrompt && (
          <motion.form
            key="form"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            onSubmit={submit}
            className="space-y-4"
          >
            <div>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value.slice(0, MAX_CHARS))}
                placeholder="Write your response here..."
                rows={4}
                required
                className="form-input resize-none font-serif"
                aria-label="Your response"
              />
              <p className={`text-right text-xs mt-1 ${content.length > MAX_CHARS * 0.9 ? 'text-amber' : 'text-earth/40'}`}>
                {content.length}/{MAX_CHARS}
              </p>
            </div>

            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value.slice(0, 30))}
              placeholder="Your first name (or leave blank to be anonymous)"
              className="form-input text-sm"
              aria-label="Display name (optional)"
            />

            {error && (
              <p className="text-red-600 text-sm" role="alert">{error}</p>
            )}

            <div className="flex justify-between items-center">
              <p className="text-earth/40 text-xs max-w-xs">
                All responses are reviewed for safety before appearing on the wall.
              </p>
              <button type="submit" disabled={submitting || !content.trim()} className="btn-primary">
                {submitting ? 'Posting...' : 'Pin to wall →'}
              </button>
            </div>
          </motion.form>
        )}
      </AnimatePresence>
    </div>
  );
}
