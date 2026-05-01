'use client';
import { useState } from 'react';
import { CheckCircle, XCircle } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';

interface Response {
  id: string;
  content: string;
  display_name: string;
  is_flagged: boolean;
  moderation_score: number | null;
  created_at: string;
  prompt?: { text: string } | null;
}

interface Props {
  flaggedResponses: Response[];
  pendingResponses: Response[];
}

export default function AdminClient({ flaggedResponses, pendingResponses }: Props) {
  const supabase = createClient();
  const [flagged, setFlagged] = useState(flaggedResponses);
  const [pending, setPending] = useState(pendingResponses);

  async function approve(id: string, isFlagged: boolean) {
    await supabase
      .from('responses')
      .update({ is_approved: true, is_flagged: false })
      .eq('id', id);

    if (isFlagged) setFlagged((prev) => prev.filter((r) => r.id !== id));
    else setPending((prev) => prev.filter((r) => r.id !== id));
  }

  async function remove(id: string, isFlagged: boolean) {
    await supabase.from('responses').delete().eq('id', id);
    if (isFlagged) setFlagged((prev) => prev.filter((r) => r.id !== id));
    else setPending((prev) => prev.filter((r) => r.id !== id));
  }

  function ResponseRow({ r, isFlagged }: { r: Response; isFlagged: boolean }) {
    return (
      <div className={`card-surface border-l-4 ${isFlagged ? 'border-red-400' : 'border-amber'}`}>
        {r.prompt && (
          <p className="text-xs text-earth/50 font-semibold uppercase tracking-wider mb-2">{r.prompt.text}</p>
        )}
        <p className="font-serif text-sm text-earth/90 mb-2 leading-relaxed">{r.content}</p>
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="text-xs text-earth/40 space-x-3">
            <span>{r.display_name}</span>
            <span>{new Date(r.created_at).toLocaleDateString()}</span>
            {r.moderation_score !== null && (
              <span className={r.moderation_score > 0.5 ? 'text-red-500' : ''}>
                Score: {r.moderation_score.toFixed(2)}
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => approve(r.id, isFlagged)}
              className="flex items-center gap-1.5 text-xs bg-green-50 text-green-700 border border-green-200 px-3 py-1.5 rounded-full hover:bg-green-100 transition-colors"
            >
              <CheckCircle className="w-3.5 h-3.5" /> Approve
            </button>
            <button
              onClick={() => remove(r.id, isFlagged)}
              className="flex items-center gap-1.5 text-xs bg-red-50 text-red-600 border border-red-200 px-3 py-1.5 rounded-full hover:bg-red-100 transition-colors"
            >
              <XCircle className="w-3.5 h-3.5" /> Remove
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Flagged */}
      <section>
        <h2 className="font-serif text-xl text-red-700 mb-4">
          Flagged for Review ({flagged.length})
        </h2>
        {flagged.length === 0 ? (
          <p className="text-earth/50 text-sm">No flagged responses.</p>
        ) : (
          <div className="space-y-3">
            {flagged.map((r) => <ResponseRow key={r.id} r={r} isFlagged />)}
          </div>
        )}
      </section>

      {/* Pending */}
      <section>
        <h2 className="font-serif text-xl text-amber mb-4">
          Pending Approval ({pending.length})
        </h2>
        {pending.length === 0 ? (
          <p className="text-earth/50 text-sm">No pending responses. ✓</p>
        ) : (
          <div className="space-y-3">
            {pending.map((r) => <ResponseRow key={r.id} r={r} isFlagged={false} />)}
          </div>
        )}
      </section>
    </div>
  );
}
