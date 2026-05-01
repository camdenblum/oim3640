'use client';
import { useState } from 'react';
import { motion } from 'framer-motion';
import type { Profile, UserBadge, Badge, Response, HPTransaction } from '@/lib/types';
import { AVATAR_ICONS, type AvatarIcon } from '@/lib/types';
import MoodGraph from './MoodGraph';

interface CheckinPoint {
  check_in_date: string;
  mood_score: number;
}

interface Props {
  profile: Profile | null;
  earnedBadges: UserBadge[];
  allBadges: Badge[];
  responses: (Response & { prompt?: { text: string } })[];
  transactions: HPTransaction[];
  checkinHistory: CheckinPoint[];
}

export default function ProfileClient({
  profile,
  earnedBadges,
  allBadges,
  responses,
  transactions,
  checkinHistory,
}: Props) {
  const [displayName, setDisplayName] = useState(profile?.display_name ?? '');
  const [avatar, setAvatar] = useState<AvatarIcon>((profile?.avatar_icon ?? 'mountain') as AvatarIcon);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [activeTab, setActiveTab] = useState<'badges' | 'cards' | 'activity'>('badges');

  const earnedSlugs = new Set(earnedBadges.map((ub) => ub.badge?.slug));

  async function saveProfile() {
    setSaving(true);
    await fetch('/api/profile', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ display_name: displayName, avatar_icon: avatar }),
    });
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  if (!profile) return <p className="text-center text-earth/50">Loading profile...</p>;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="card-surface">
        <div className="flex flex-col sm:flex-row gap-6 items-start sm:items-center">
          <div className="w-20 h-20 rounded-full bg-forest/10 flex items-center justify-center text-4xl border-2 border-forest/20">
            {AVATAR_ICONS[avatar]}
          </div>
          <div className="flex-1">
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value.slice(0, 40))}
              placeholder="Your name (or stay anonymous)"
              className="form-input mb-2 font-serif text-lg"
              aria-label="Display name"
            />
            <div className="flex flex-wrap gap-2 mb-3">
              {(Object.entries(AVATAR_ICONS) as [AvatarIcon, string][]).map(([key, emoji]) => (
                <button
                  key={key}
                  onClick={() => setAvatar(key)}
                  aria-label={`Avatar: ${key}`}
                  aria-pressed={avatar === key}
                  className={`text-2xl w-10 h-10 rounded-full transition-all ${
                    avatar === key
                      ? 'bg-forest/15 ring-2 ring-forest'
                      : 'hover:bg-forest/5'
                  }`}
                >
                  {emoji}
                </button>
              ))}
            </div>
            <button onClick={saveProfile} disabled={saving} className="btn-primary text-sm py-2 px-4">
              {saving ? 'Saving...' : saved ? '✓ Saved!' : 'Save profile'}
            </button>
          </div>
          <div className="text-center">
            <div className="hp-chip text-lg px-5 py-2.5 mb-1">
              🌿 {profile.healing_points.toLocaleString()}
            </div>
            <p className="text-xs text-earth/50">Healing Points</p>
            {profile.login_streak > 1 && (
              <p className="text-xs text-amber mt-1">🔥 {profile.login_streak}-day streak</p>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-earth/10">
        {(['badges', 'cards', 'activity'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2.5 text-sm font-medium capitalize transition-colors border-b-2 -mb-px ${
              activeTab === tab
                ? 'border-forest text-forest'
                : 'border-transparent text-earth/50 hover:text-earth'
            }`}
          >
            {tab === 'badges' ? 'Badges' : tab === 'cards' ? 'My Cards' : 'HP Activity'}
          </button>
        ))}
      </div>

      {/* Badges tab */}
      {activeTab === 'badges' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {allBadges.map((badge) => {
              const earned = earnedSlugs.has(badge.slug);
              const earnedData = earnedBadges.find((ub) => ub.badge?.slug === badge.slug);
              return (
                <div
                  key={badge.id}
                  className={`rounded-2xl border p-4 text-center transition-all ${
                    earned
                      ? 'bg-forest/5 border-forest/20'
                      : 'bg-white/30 border-earth/10 opacity-40'
                  }`}
                  title={badge.description ?? badge.name}
                >
                  <p className="text-3xl mb-2">{badge.icon ?? '🏅'}</p>
                  <p className="text-xs font-semibold text-forest leading-tight">{badge.name}</p>
                  {earned && earnedData && (
                    <p className="text-[10px] text-earth/40 mt-1">
                      {new Date(earnedData.earned_at).toLocaleDateString()}
                    </p>
                  )}
                  {!earned && (
                    <p className="text-[10px] text-earth/40 mt-1 leading-tight">{badge.description}</p>
                  )}
                </div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* Cards tab */}
      {activeTab === 'cards' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {responses.length === 0 ? (
            <p className="text-earth/50 text-center py-8">
              You haven&apos;t added any cards yet. Head to{' '}
              <a href="/" className="text-forest underline">the wall</a> to share your voice.
            </p>
          ) : (
            <div className="space-y-3">
              {responses.map((r) => (
                <div key={r.id} className="card-surface">
                  {r.prompt && (
                    <p className="text-xs text-earth/50 font-semibold uppercase tracking-wider mb-2">
                      {r.prompt.text}
                    </p>
                  )}
                  <p className="font-serif text-earth/90 leading-relaxed">&ldquo;{r.content}&rdquo;</p>
                  <div className="flex justify-between items-center mt-3">
                    <p className="text-xs text-earth/40">
                      {new Date(r.created_at).toLocaleDateString()}
                    </p>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      r.is_approved
                        ? 'bg-green-50 text-green-700'
                        : r.is_flagged
                        ? 'bg-red-50 text-red-600'
                        : 'bg-amber/10 text-amber'
                    }`}>
                      {r.is_approved ? 'Live on wall' : r.is_flagged ? 'Under review' : 'Pending'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {/* Activity tab */}
      {activeTab === 'activity' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          {checkinHistory.length > 1 && (
            <div className="card-surface">
              <h3 className="font-serif text-lg text-forest mb-1">Mood history</h3>
              <p className="text-xs text-earth/40 mb-4">Private — only you can see this</p>
              <MoodGraph history={checkinHistory} />
            </div>
          )}
          <div className="card-surface">
            <h3 className="font-serif text-lg text-forest mb-4">Recent HP activity</h3>
            {transactions.length === 0 ? (
              <p className="text-earth/50 text-sm">No activity yet.</p>
            ) : (
              <ul className="divide-y divide-earth/10">
                {transactions.map((tx) => (
                  <li key={tx.id} className="flex justify-between items-center py-2.5 text-sm">
                    <span className="text-earth/70">{tx.description ?? tx.reason_code}</span>
                    <span className={`font-semibold ${tx.amount > 0 ? 'text-forest' : 'text-red-500'}`}>
                      {tx.amount > 0 ? '+' : ''}{tx.amount} HP
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
}
