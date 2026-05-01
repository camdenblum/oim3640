import { createClient } from '@/lib/supabase/server';
import WallGrid from '@/components/wall/WallGrid';
import Link from 'next/link';

export const revalidate = 30;

export default async function WallPage() {
  const supabase = await createClient();

  const [{ data: prompts }, { data: responses }, { data: { user } }] = await Promise.all([
    supabase.from('prompts').select('*').eq('is_active', true).order('display_order'),
    supabase
      .from('responses')
      .select('*, prompt:prompts(id, text), reaction_counts:response_reaction_counts(*)')
      .eq('is_approved', true)
      .eq('is_flagged', false)
      .order('created_at', { ascending: false })
      .limit(120),
    supabase.auth.getUser(),
  ]);

  let userReactions: Record<string, string[]> = {};
  let respondedPrompts: string[] = [];

  if (user) {
    const responseIds = (responses ?? []).map((r) => r.id);
    if (responseIds.length > 0) {
      const { data: rxns } = await supabase
        .from('reactions')
        .select('response_id, reaction_type')
        .eq('user_id', user.id)
        .in('response_id', responseIds);

      rxns?.forEach(({ response_id, reaction_type }) => {
        userReactions[response_id] ??= [];
        userReactions[response_id].push(reaction_type);
      });
    }

    const { data: mine } = await supabase
      .from('responses')
      .select('prompt_id')
      .eq('user_id', user.id);
    respondedPrompts = mine?.map((r) => r.prompt_id) ?? [];
  }

  const emptyState = (responses ?? []).length === 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Hero */}
      <section className="text-center py-16 md:py-20">
        <p className="text-forest/60 text-sm font-semibold uppercase tracking-widest mb-3">
          The Busyhead Project
        </p>
        <h1 className="font-serif text-4xl md:text-5xl lg:text-6xl text-forest mb-5 leading-tight">
          The Community Wall
        </h1>
        <p className="text-earth/80 max-w-xl mx-auto text-lg leading-relaxed mb-8">
          Over 11,000 handwritten cards. One shared truth: you are not alone.
          Add your voice. Read theirs.
        </p>
        {!user && (
          <Link href="/auth" className="btn-primary text-base px-8 py-3 inline-block">
            Add your voice →
          </Link>
        )}
      </section>

      {/* Wall */}
      <WallGrid
        initialResponses={responses ?? []}
        prompts={prompts ?? []}
        userId={user?.id ?? null}
        userReactions={userReactions}
        respondedPrompts={respondedPrompts}
        emptyState={emptyState}
      />
    </div>
  );
}
