import { createClient } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';
import ProfileClient from '@/components/profile/ProfileClient';

export default async function ProfilePage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect('/auth?next=/profile');

  const [profileRes, badgesRes, responsesRes, txRes] = await Promise.all([
    supabase.from('profiles').select('*').eq('id', user.id).single(),
    supabase.from('user_badges').select('*, badge:badges(*)').eq('user_id', user.id).order('earned_at', { ascending: false }),
    supabase.from('responses').select('*, prompt:prompts(text)').eq('user_id', user.id).order('created_at', { ascending: false }),
    supabase.from('hp_transactions').select('*').eq('user_id', user.id).order('created_at', { ascending: false }).limit(20),
  ]);

  const { data: checkinHistory } = await supabase
    .from('daily_checkins')
    .select('check_in_date, mood_score')
    .eq('user_id', user.id)
    .order('check_in_date', { ascending: true })
    .limit(30);

  const { data: allBadges } = await supabase.from('badges').select('*').order('condition_value');

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <ProfileClient
        profile={profileRes.data}
        earnedBadges={badgesRes.data ?? []}
        allBadges={allBadges ?? []}
        responses={responsesRes.data ?? []}
        transactions={txRes.data ?? []}
        checkinHistory={checkinHistory ?? []}
      />
    </div>
  );
}
