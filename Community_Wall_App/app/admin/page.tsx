import { createClient } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';
import AdminClient from '@/components/admin/AdminClient';

const ADMIN_EMAILS = (process.env.ADMIN_EMAILS ?? '').split(',').map((e) => e.trim().toLowerCase());

export default async function AdminPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user || !ADMIN_EMAILS.includes(user.email?.toLowerCase() ?? '')) {
    redirect('/');
  }

  const [flagged, pending, stats] = await Promise.all([
    supabase
      .from('responses')
      .select('*, prompt:prompts(text)')
      .eq('is_flagged', true)
      .order('created_at', { ascending: false })
      .limit(50),
    supabase
      .from('responses')
      .select('*, prompt:prompts(text)')
      .eq('is_approved', false)
      .eq('is_flagged', false)
      .order('created_at', { ascending: false })
      .limit(50),
    Promise.all([
      supabase.from('responses').select('*', { count: 'exact', head: true }),
      supabase.from('profiles').select('*', { count: 'exact', head: true }),
      supabase.from('reactions').select('*', { count: 'exact', head: true }),
      supabase.from('daily_checkins').select('*', { count: 'exact', head: true }),
    ]),
  ]);

  const [respCount, userCount, rxnCount, checkinCount] = stats;

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      <h1 className="section-header mb-2">Admin Dashboard</h1>
      <p className="text-earth/60 text-sm mb-8">Logged in as {user.email}</p>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        {[
          { label: 'Total Cards', value: respCount.count ?? 0 },
          { label: 'Community Members', value: userCount.count ?? 0 },
          { label: 'Total Reactions', value: rxnCount.count ?? 0 },
          { label: 'Daily Check-ins', value: checkinCount.count ?? 0 },
        ].map(({ label, value }) => (
          <div key={label} className="card-surface text-center">
            <p className="font-serif text-3xl text-forest font-semibold">{value.toLocaleString()}</p>
            <p className="text-earth/60 text-xs mt-1">{label}</p>
          </div>
        ))}
      </div>

      <AdminClient
        flaggedResponses={flagged.data ?? []}
        pendingResponses={pending.data ?? []}
      />
    </div>
  );
}
