import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { createServiceClient } from '@/lib/supabase/server';
import { moderateContent } from '@/lib/moderation';
import { awardHP, checkAndAwardBadge } from '@/lib/hp';

export async function GET(req: NextRequest) {
  const supabase = await createClient();
  const { searchParams } = new URL(req.url);
  const promptId = searchParams.get('prompt_id');

  let query = supabase
    .from('responses')
    .select('*, prompt:prompts(id, text), reaction_counts:response_reaction_counts(*)')
    .eq('is_approved', true)
    .eq('is_flagged', false)
    .order('created_at', { ascending: false })
    .limit(100);

  if (promptId) query = query.eq('prompt_id', promptId);

  const { data, error } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ responses: data });
}

export async function POST(req: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const body = await req.json();
  const { prompt_id, content, display_name } = body;

  if (!prompt_id || !content?.trim()) {
    return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
  }

  if (content.length > 500) {
    return NextResponse.json({ error: 'Response too long (max 500 characters)' }, { status: 400 });
  }

  const modResult = await moderateContent(content);

  if (modResult.crisis) {
    const serviceClient = await createServiceClient();
    await serviceClient.from('responses').insert({
      user_id: user.id,
      prompt_id,
      content,
      display_name: display_name || 'a voice from the community',
      is_approved: false,
      is_flagged: true,
      moderation_score: modResult.score,
    });
    return NextResponse.json({ crisis: true }, { status: 200 });
  }

  const serviceClient = await createServiceClient();
  const { data: response, error } = await serviceClient
    .from('responses')
    .insert({
      user_id: user.id,
      prompt_id,
      content,
      display_name: display_name || 'a voice from the community',
      is_approved: !modResult.flagged,
      is_flagged: modResult.flagged,
      moderation_score: modResult.score,
    })
    .select()
    .single();

  if (error) {
    if (error.code === '23505') {
      return NextResponse.json({ error: 'Already responded to this prompt' }, { status: 409 });
    }
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  const { count: responseCount } = await serviceClient
    .from('responses')
    .select('*', { count: 'exact', head: true })
    .eq('user_id', user.id);

  const isFirst = (responseCount ?? 0) === 1;
  await awardHP(user.id, isFirst ? 'first_response' : 'submit_response', 'Wall response submitted');
  if (isFirst) await checkAndAwardBadge(user.id, 'first_step');

  const { count: cycleCount } = await serviceClient
    .from('responses')
    .select('*', { count: 'exact', head: true })
    .eq('user_id', user.id)
    .gte('created_at', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString());

  if ((cycleCount ?? 0) >= 5) await checkAndAwardBadge(user.id, 'busyhead');

  return NextResponse.json({ response }, { status: 201 });
}
