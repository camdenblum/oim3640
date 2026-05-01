'use client';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { StoreItem } from '@/lib/types';
import Link from 'next/link';

const CATEGORY_META: Record<string, { emoji: string; label: string; color: string }> = {
  digital:  { emoji: '🖼️', label: 'Digital Download', color: 'bg-sky/10 text-sky border-sky/20' },
  giveaway: { emoji: '🎁', label: 'Monthly Giveaway',  color: 'bg-amber/10 text-amber border-amber/20' },
  discount: { emoji: '🏷️', label: 'Discount Code',    color: 'bg-green-50 text-green-700 border-green-200' },
  wall:     { emoji: '📌', label: 'Wall Recognition',  color: 'bg-forest/10 text-forest border-forest/20' },
};

interface Props {
  items: StoreItem[];
  userHP: number;
  userId: string | null;
  redeemedItemIds: string[];
}

export default function StoreClient({ items, userHP, userId, redeemedItemIds }: Props) {
  const [redeeming, setRedeeming] = useState<string | null>(null);
  const [redeemed, setRedeemed] = useState<Set<string>>(new Set(redeemedItemIds));
  const [currentHP, setCurrentHP] = useState(userHP);
  const [error, setError] = useState('');
  const [confirm, setConfirm] = useState<StoreItem | null>(null);

  async function redeem(item: StoreItem) {
    if (!userId || redeeming) return;
    setRedeeming(item.id);
    setError('');

    const res = await fetch('/api/store', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: item.id }),
    });

    const data = await res.json();
    setRedeeming(null);
    setConfirm(null);

    if (!res.ok) {
      setError(data.error ?? 'Something went wrong');
      return;
    }

    setRedeemed((prev) => new Set([...prev, item.id]));
    setCurrentHP((prev) => prev - item.hp_cost);
  }

  const categories = Array.from(new Set(items.map((i) => i.category)));

  return (
    <div>
      {error && (
        <p className="text-red-600 text-sm mb-4 text-center" role="alert">{error}</p>
      )}

      {!userId && (
        <div className="text-center mb-8 card-surface">
          <p className="text-earth/70 text-sm mb-3">Sign in to spend your Healing Points</p>
          <Link href="/auth" className="btn-primary inline-block">Join the wall →</Link>
        </div>
      )}

      {categories.map((cat) => {
        const catItems = items.filter((i) => i.category === cat);
        const meta = CATEGORY_META[cat] ?? CATEGORY_META.digital;
        return (
          <section key={cat} className="mb-10">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xl" aria-hidden>{meta.emoji}</span>
              <h2 className="font-serif text-lg text-forest">{meta.label}</h2>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {catItems.map((item) => {
                const hasEnough = currentHP >= item.hp_cost;
                const alreadyRedeemed = redeemed.has(item.id);
                return (
                  <div
                    key={item.id}
                    className={`card-surface flex flex-col transition-all ${
                      !hasEnough && !alreadyRedeemed ? 'opacity-60' : ''
                    }`}
                  >
                    <div className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-full border mb-3 w-fit ${meta.color}`}>
                      {meta.emoji} {meta.label}
                    </div>
                    <h3 className="font-serif text-base text-forest mb-2 leading-snug">{item.name}</h3>
                    {item.description && (
                      <p className="text-earth/60 text-sm leading-relaxed flex-1 mb-4">{item.description}</p>
                    )}
                    <div className="flex items-center justify-between mt-auto">
                      <span className="hp-chip text-sm">🌿 {item.hp_cost.toLocaleString()} HP</span>
                      {alreadyRedeemed ? (
                        <span className="text-xs text-green-700 font-semibold">✓ Redeemed</span>
                      ) : !userId ? (
                        <Link href="/auth" className="btn-secondary text-xs py-1.5 px-3">Sign in</Link>
                      ) : (
                        <button
                          onClick={() => setConfirm(item)}
                          disabled={!hasEnough || !!redeeming}
                          className="btn-primary text-xs py-1.5 px-4 disabled:opacity-40"
                          title={!hasEnough ? `You need ${item.hp_cost - currentHP} more HP` : undefined}
                        >
                          Redeem
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        );
      })}

      {/* Confirm modal */}
      <AnimatePresence>
        {confirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 px-4"
            onClick={() => setConfirm(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-cream rounded-2xl p-8 max-w-sm w-full shadow-xl"
            >
              <h3 className="font-serif text-xl text-forest mb-2">Confirm redemption</h3>
              <p className="text-earth/70 text-sm mb-1">{confirm.name}</p>
              <p className="hp-chip inline-flex mb-6">🌿 {confirm.hp_cost.toLocaleString()} HP</p>
              <div className="flex gap-3">
                <button
                  onClick={() => redeem(confirm)}
                  disabled={!!redeeming}
                  className="btn-primary flex-1"
                >
                  {redeeming === confirm.id ? 'Redeeming...' : 'Yes, redeem'}
                </button>
                <button onClick={() => setConfirm(null)} className="btn-secondary">
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
