import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { createServiceClient } from '@/lib/supabase/server';
import { awardHP, checkAndAwardBadge } from '@/lib/hp';

export async function GET() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { data: profile } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .single();

  const { data: badges } = await supabase
    .from('user_badges')
    .select('*, badge:badges(*)')
    .eq('user_id', user.id)
    .order('earned_at', { ascending: false });

  const { data: responses } = await supabase
    .from('responses')
    .select('*, prompt:prompts(text)')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false });

  const { data: transactions } = await supabase
    .from('hp_transactions')
    .select('*')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })
    .limit(20);

  return NextResponse.json({ profile, badges, responses, transactions });
}

export async function PATCH(req: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const body = await req.json();
  const allowed = ['display_name', 'avatar_icon', 'opt_out_leaderboard', 'trigger_warnings_enabled'];
  const updates: Record<string, unknown> = {};
  for (const key of allowed) {
    if (key in body) updates[key] = body[key];
  }

  updates.updated_at = new Date().toISOString();

  const { data: current } = await supabase
    .from('profiles')
    .select('profile_completed')
    .eq('id', user.id)
    .single();

  const { data: profile, error } = await supabase
    .from('profiles')
    .update(updates)
    .eq('id', user.id)
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  if (!current?.profile_completed && updates.display_name) {
    const serviceClient = await createServiceClient();
    await serviceClient
      .from('profiles')
      .update({ profile_completed: true })
      .eq('id', user.id);
    await awardHP(user.id, 'profile_complete', 'Completed profile setup');
    await checkAndAwardBadge(user.id, 'profile_complete');
  }

  return NextResponse.json({ profile });
}
