'use client';
import { useState } from 'react';
import { motion } from 'framer-motion';
import { Share2 } from 'lucide-react';
import { REACTIONS, type ReactionType, type Response } from '@/lib/types';

const CARD_COLORS = ['notecard-cream', 'notecard-yellow', 'notecard-blue', 'notecard-green'];

function cardColor(id: string): string {
  const sum = id.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
  return CARD_COLORS[sum % CARD_COLORS.length];
}

function cardRotation(id: string): number {
  const sum = id.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
  return ((sum % 5) - 2) * 0.6;
}

interface Props {
  response: Response;
  userId: string | null;
  userReactions: string[];
  showTriggerWarning?: boolean;
  index?: number;
}

export default function NoteCard({ response, userId, userReactions, showTriggerWarning = false, index = 0 }: Props) {
  const [revealed, setRevealed] = useState(!showTriggerWarning);
  const [localReactions, setLocalReactions] = useState<ReactionType[]>(userReactions as ReactionType[]);
  const [counts, setCounts] = useState<Record<ReactionType, number>>({
    leaf:      response.reaction_counts?.leaf_count ?? 0,
    heart:     response.reaction_counts?.heart_count ?? 0,
    lightbulb: response.reaction_counts?.lightbulb_count ?? 0,
    mountain:  response.reaction_counts?.mountain_count ?? 0,
  });
  const [reacting, setReacting] = useState(false);

  const rotation = cardRotation(response.id);
  const color = cardColor(response.id);

  async function toggleReaction(type: ReactionType) {
    if (!userId || reacting) return;
    setReacting(true);

    const isActive = localReactions.includes(type);
    setLocalReactions((prev) =>
      isActive ? prev.filter((r) => r !== type) : [...prev, type]
    );
    setCounts((prev) => ({
      ...prev,
      [type]: Math.max(0, prev[type] + (isActive ? -1 : 1)),
    }));

    await fetch('/api/reactions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ response_id: response.id, reaction_type: type }),
    });
    setReacting(false);
  }

  const promptText = (response.prompt as { text?: string } | undefined)?.text;

  return (
    <motion.div
      className="wall-card-wrap"
      initial={{ opacity: 0, y: 20, rotate: rotation }}
      animate={{ opacity: 1, y: 0, rotate: rotation }}
      transition={{ duration: 0.4, delay: index * 0.04, ease: 'easeOut' }}
      whileHover={{ y: -3, rotate: rotation * 0.5, transition: { duration: 0.2 } }}
    >
      <article
        className={`notecard ${color} p-5 cursor-default group`}
        style={{ transform: `rotate(${rotation}deg)` }}
        aria-label={`Community wall card from ${response.display_name}`}
      >
        {/* Prompt label */}
        {promptText && (
          <p className="text-[10px] font-semibold uppercase tracking-wider text-earth/40 mb-3 leading-tight line-clamp-2">
            {promptText}
          </p>
        )}

        {/* Content */}
        {!revealed ? (
          <div className="text-center py-4">
            <p className="text-earth/50 text-xs mb-3">
              This card may touch on difficult topics.
            </p>
            <button
              onClick={() => setRevealed(true)}
              className="text-xs text-forest underline underline-offset-2"
            >
              Show card
            </button>
          </div>
        ) : (
          <p className="font-serif text-base leading-relaxed text-gray-800 mb-4">
            &ldquo;{response.content}&rdquo;
          </p>
        )}

        {/* Footer */}
        <div className="flex items-end justify-between gap-2 mt-3">
          <p className="text-xs text-earth/50 italic">{response.display_name}</p>
          <button
            onClick={() => {
              if (navigator.share) {
                navigator.share({
                  title: 'From the Busyhead Community Wall',
                  text: `"${response.content}" — ${response.display_name}`,
                  url: window.location.origin,
                }).catch(() => {});
              }
            }}
            aria-label="Share this card"
            className="opacity-0 group-hover:opacity-100 transition-opacity text-earth/30 hover:text-forest"
          >
            <Share2 className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Reactions */}
        {revealed && (
          <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-earth/10">
            {(Object.entries(REACTIONS) as [ReactionType, { emoji: string; label: string }][]).map(([type, { emoji, label }]) => {
              const active = localReactions.includes(type);
              return (
                <button
                  key={type}
                  onClick={() => toggleReaction(type)}
                  disabled={!userId}
                  aria-label={`${label}${counts[type] > 0 ? ` · ${counts[type]}` : ''}`}
                  aria-pressed={active}
                  title={userId ? label : 'Sign in to react'}
                  className={`reaction-btn text-xs ${
                    active
                      ? 'reaction-btn-active'
                      : 'text-earth/50 hover:text-forest hover:bg-forest/5'
                  } disabled:cursor-default`}
                >
                  <span aria-hidden>{emoji}</span>
                  {counts[type] > 0 && (
                    <span className="text-[10px] font-medium">{counts[type]}</span>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </article>
    </motion.div>
  );
}
