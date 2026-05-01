import { createClient } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';
import DailyCheckinClient from '@/components/checkin/DailyCheckinClient';

export default async function CheckinPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect('/auth?next=/checkin');

  const today = new Date().toISOString().split('T')[0];
  const { data: existing } = await supabase
    .from('daily_checkins')
    .select('*')
    .eq('user_id', user.id)
    .eq('check_in_date', today)
    .single();

  const { data: history } = await supabase
    .from('daily_checkins')
    .select('check_in_date, mood_score')
    .eq('user_id', user.id)
    .order('check_in_date', { ascending: false })
    .limit(30);

  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <header className="text-center mb-10">
        <h1 className="section-header mb-3">Daily Moment</h1>
        <p className="text-earth/70">
          Two minutes, just for you. No one else sees this.
        </p>
      </header>
      <DailyCheckinClient
        alreadyCheckedIn={!!existing}
        existingCheckin={existing}
        history={history ?? []}
      />
    </div>
  );
}
