import { createClient } from '@/lib/supabase/server';
import StoreClient from '@/components/store/StoreClient';

export const revalidate = 300;

export default async function StorePage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  const { data: items } = await supabase
    .from('store_items')
    .select('*')
    .eq('is_available', true)
    .order('hp_cost');

  let profile = null;
  let redemptions: unknown[] = [];
  if (user) {
    const [p, r] = await Promise.all([
      supabase.from('profiles').select('healing_points').eq('id', user.id).single(),
      supabase.from('redemptions').select('item_id').eq('user_id', user.id),
    ]);
    profile = p.data;
    redemptions = r.data ?? [];
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      <header className="text-center mb-12">
        <p className="text-forest/60 text-xs font-semibold uppercase tracking-widest mb-2">
          Earn. Redeem. Give back.
        </p>
        <h1 className="section-header mb-3">The Merch Tent</h1>
        <p className="text-earth/70 max-w-lg mx-auto text-sm leading-relaxed">
          Healing Points are earned by showing up, sharing honestly, and supporting each other.
          They can never be purchased — only given.
        </p>
        {user && profile && (
          <div className="hp-chip mt-4 text-base mx-auto inline-flex">
            🌿 {profile.healing_points.toLocaleString()} HP
          </div>
        )}
      </header>

      <StoreClient
        items={items ?? []}
        userHP={profile?.healing_points ?? 0}
        userId={user?.id ?? null}
        redeemedItemIds={(redemptions as { item_id: string }[]).map((r) => r.item_id)}
      />

      <div className="mt-12 text-center border-t border-earth/10 pt-8">
        <p className="text-earth/60 text-sm mb-3">
          Want to support the mission directly?
        </p>
        <a
          href="https://givebutter.com/thebusyheadproject"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary inline-block"
        >
          Donate to The Busyhead Project →
        </a>
      </div>
    </div>
  );
}
