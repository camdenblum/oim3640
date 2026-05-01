'use client';
import { useEffect, useState, useCallback } from 'react';
import { createClient } from '@/lib/supabase/client';
import { motion } from 'framer-motion';
import { Shuffle, Filter } from 'lucide-react';
import NoteCard from './NoteCard';
import SubmitForm from './SubmitForm';
import type { Response, Prompt } from '@/lib/types';

interface Props {
  initialResponses: Response[];
  prompts: Prompt[];
  userId: string | null;
  userReactions: Record<string, string[]>;
  respondedPrompts: string[];
  emptyState: boolean;
}

export default function WallGrid({
  initialResponses,
  prompts,
  userId,
  userReactions: initialUserReactions,
  respondedPrompts: initialRespondedPrompts,
  emptyState,
}: Props) {
  const [responses, setResponses] = useState<Response[]>(initialResponses);
  const [userReactions, setUserReactions] = useState(initialUserReactions);
  const [respondedPrompts, setRespondedPrompts] = useState(initialRespondedPrompts);
  const [filterPromptId, setFilterPromptId] = useState<string | null>(null);
  const [shuffled, setShuffled] = useState(false);
  const supabase = createClient();

  // Real-time: new approved responses appear live
  useEffect(() => {
    const channel = supabase
      .channel('wall-live')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'responses', filter: 'is_approved=eq.true' },
        (payload) => {
          setResponses((prev) => {
            if (prev.some((r) => r.id === payload.new.id)) return prev;
            return [payload.new as Response, ...prev];
          });
        }
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [supabase]);

  function shuffle() {
    setResponses((prev) => [...prev].sort(() => Math.random() - 0.5));
    setShuffled(true);
    setTimeout(() => setShuffled(false), 1200);
  }

  const handleNewResponse = useCallback((newResponse: Response) => {
    setResponses((prev) => [newResponse, ...prev]);
    setRespondedPrompts((prev) => [...prev, newResponse.prompt_id]);
  }, []);

  const displayed = filterPromptId
    ? responses.filter((r) => r.prompt_id === filterPromptId)
    : responses;

  return (
    <section>
      <SubmitForm
        prompts={prompts}
        userId={userId}
        respondedPrompts={respondedPrompts}
        onSubmitted={handleNewResponse}
      />

      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="w-4 h-4 text-earth/40" aria-hidden />
          <button
            onClick={() => setFilterPromptId(null)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
              !filterPromptId
                ? 'bg-forest text-cream border-forest'
                : 'border-earth/20 text-earth/60 hover:border-forest/30'
            }`}
          >
            All voices
          </button>
          {prompts.map((p) => (
            <button
              key={p.id}
              onClick={() => setFilterPromptId(filterPromptId === p.id ? null : p.id)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
                filterPromptId === p.id
                  ? 'bg-forest text-cream border-forest'
                  : 'border-earth/20 text-earth/60 hover:border-forest/30'
              }`}
            >
              {p.display_order}
            </button>
          ))}
        </div>

        <motion.button
          onClick={shuffle}
          animate={shuffled ? { rotate: 180 } : { rotate: 0 }}
          transition={{ duration: 0.4 }}
          className="btn-ghost text-xs flex items-center gap-1.5"
          aria-label="Shuffle wall"
        >
          <Shuffle className="w-4 h-4" />
          Shuffle wall
        </motion.button>
      </div>

      {/* Prompt legend */}
      {filterPromptId && (
        <div className="bg-forest/5 border border-forest/15 rounded-xl px-4 py-3 mb-6 text-sm text-forest/80 font-serif italic">
          &ldquo;{prompts.find((p) => p.id === filterPromptId)?.text}&rdquo;
        </div>
      )}

      {/* Wall */}
      {displayed.length === 0 ? (
        <div className="text-center py-24 text-earth/50">
          <p className="text-4xl mb-4">🌿</p>
          <p className="font-serif text-lg">
            {emptyState
              ? 'The wall is waiting for your voice. Be the first to share.'
              : 'No cards match this filter yet.'}
          </p>
        </div>
      ) : (
        <div className="wall-grid" role="feed" aria-label="Community wall cards">
          {displayed.map((response, i) => (
            <NoteCard
              key={response.id}
              response={response}
              userId={userId}
              userReactions={userReactions[response.id] ?? []}
              index={i}
            />
          ))}
        </div>
      )}
    </section>
  );
}
