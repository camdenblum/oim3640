import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { createServiceClient } from '@/lib/supabase/server';

export async function GET() {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from('store_items')
    .select('*')
    .eq('is_available', true)
    .order('hp_cost');

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ items: data });
}

export async function POST(req: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { item_id } = await req.json();
  if (!item_id) return NextResponse.json({ error: 'Missing item_id' }, { status: 400 });

  const { data: item } = await supabase
    .from('store_items')
    .select('*')
    .eq('id', item_id)
    .eq('is_available', true)
    .single();

  if (!item) return NextResponse.json({ error: 'Item not found' }, { status: 404 });

  const { data: profile } = await supabase
    .from('profiles')
    .select('healing_points')
    .eq('id', user.id)
    .single();

  if (!profile || profile.healing_points < item.hp_cost) {
    return NextResponse.json({ error: 'Not enough Healing Points' }, { status: 402 });
  }

  const serviceClient = await createServiceClient();

  await serviceClient
    .from('profiles')
    .update({ healing_points: profile.healing_points - item.hp_cost })
    .eq('id', user.id);

  await serviceClient.from('hp_transactions').insert({
    user_id: user.id,
    amount: -item.hp_cost,
    reason_code: 'store_redemption',
    description: `Redeemed: ${item.name}`,
  });

  const { data: redemption, error } = await serviceClient
    .from('redemptions')
    .insert({ user_id: user.id, item_id, hp_spent: item.hp_cost })
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ redemption }, { status: 201 });
}
