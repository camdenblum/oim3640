import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { createServiceClient } from '@/lib/supabase/server';
import { awardHP, checkReactionBadge } from '@/lib/hp';
import type { ReactionType } from '@/lib/types';

export async function POST(req: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { response_id, reaction_type } = await req.json() as {
    response_id: string;
    reaction_type: ReactionType;
  };

  const valid: ReactionType[] = ['leaf', 'heart', 'lightbulb', 'mountain'];
  if (!response_id || !valid.includes(reaction_type)) {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
  }

  const serviceClient = await createServiceClient();
  const today = new Date().toISOString().split('T')[0];
  const { count: todayCount } = await serviceClient
    .from('reactions')
    .select('*', { count: 'exact', head: true })
    .eq('user_id', user.id)
    .gte('created_at', `${today}T00:00:00.000Z`);

  const { data: existing } = await serviceClient
    .from('reactions')
    .select('id')
    .eq('user_id', user.id)
    .eq('response_id', response_id)
    .eq('reaction_type', reaction_type)
    .single();

  if (existing) {
    await serviceClient.from('reactions').delete().eq('id', existing.id);
    return NextResponse.json({ toggled: 'removed' });
  }

  const { error } = await serviceClient.from('reactions').insert({
    user_id: user.id,
    response_id,
    reaction_type,
  });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  if ((todayCount ?? 0) < 20) {
    await awardHP(user.id, 'daily_reaction', 'Reacted to a card');
  }

  await checkReactionBadge(user.id);

  return NextResponse.json({ toggled: 'added' }, { status: 201 });
}
