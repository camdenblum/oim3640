import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { createServiceClient } from '@/lib/supabase/server';
import { awardHP } from '@/lib/hp';

export async function GET() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const today = new Date().toISOString().split('T')[0];
  const { data } = await supabase
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

  return NextResponse.json({ today: data, history: history ?? [] });
}

export async function POST(req: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { mood_score, journal_text, completed_breathing } = await req.json();

  if (typeof mood_score !== 'number' || mood_score < 1 || mood_score > 5) {
    return NextResponse.json({ error: 'Invalid mood score' }, { status: 400 });
  }

  const today = new Date().toISOString().split('T')[0];
  const serviceClient = await createServiceClient();

  const { data: existing } = await serviceClient
    .from('daily_checkins')
    .select('id')
    .eq('user_id', user.id)
    .eq('check_in_date', today)
    .single();

  if (existing) {
    return NextResponse.json({ error: 'Already checked in today' }, { status: 409 });
  }

  const { data, error } = await serviceClient
    .from('daily_checkins')
    .insert({
      user_id: user.id,
      mood_score,
      journal_text: journal_text ?? null,
      completed_breathing: completed_breathing ?? false,
      check_in_date: today,
    })
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  await awardHP(user.id, 'daily_checkin', 'Completed daily check-in');

  return NextResponse.json({ checkin: data }, { status: 201 });
}
