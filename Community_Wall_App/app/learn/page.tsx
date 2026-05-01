import { createClient } from '@/lib/supabase/server';
import type { Resource } from '@/lib/types';
import Link from 'next/link';
import { BookOpen, Heart, Lightbulb, Music, ExternalLink } from 'lucide-react';

export const revalidate = 3600;

const CATEGORY_META: Record<string, { label: string; Icon: React.ElementType; color: string }> = {
  tip:        { label: 'Tip',        Icon: Lightbulb, color: 'text-amber bg-amber/10 border-amber/20' },
  resource:   { label: 'Resource',   Icon: BookOpen,  color: 'text-forest bg-forest/10 border-forest/20' },
  fact:       { label: 'Did You Know?', Icon: Heart,  color: 'text-sky bg-sky/10 border-sky/20' },
  reflection: { label: 'Reflection', Icon: Music,     color: 'text-earth bg-earth/10 border-earth/20' },
  lyric:      { label: "Noah's Words", Icon: Music,   color: 'text-earth bg-earth/10 border-earth/20' },
};

function ResourceCard({ resource }: { resource: Resource }) {
  const meta = CATEGORY_META[resource.category] ?? CATEGORY_META.tip;
  const { Icon } = meta;

  return (
    <article className="card-surface h-full flex flex-col">
      <div className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-full border mb-4 w-fit ${meta.color}`}>
        <Icon className="w-3.5 h-3.5" aria-hidden />
        {meta.label}
      </div>
      <h3 className="font-serif text-lg text-forest mb-3 leading-snug">{resource.title}</h3>
      {resource.body && (
        <p className="text-earth/80 text-sm leading-relaxed flex-1">{resource.body}</p>
      )}
      <div className="mt-4 flex items-center justify-between">
        {resource.source_name && (
          <span className="text-xs text-earth/50">{resource.source_name}</span>
        )}
        {resource.source_url && (
          <a
            href={resource.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-forest font-medium hover:underline"
          >
            Visit <ExternalLink className="w-3 h-3" aria-hidden />
          </a>
        )}
      </div>
    </article>
  );
}

export default async function LearnPage() {
  const supabase = await createClient();
  const { data: resources } = await supabase
    .from('resources')
    .select('*')
    .eq('is_active', true)
    .order('created_at');

  const tips       = resources?.filter((r) => r.category === 'tip') ?? [];
  const facts      = resources?.filter((r) => r.category === 'fact') ?? [];
  const links      = resources?.filter((r) => r.category === 'resource') ?? [];
  const lyrics     = resources?.filter((r) => r.category === 'lyric' || r.category === 'reflection') ?? [];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12">
      <header className="mb-12 text-center">
        <h1 className="section-header mb-3">The Other Place</h1>
        <p className="text-earth/70 max-w-lg mx-auto leading-relaxed">
          Resources, reflections, and small truths — gathered to help you and the people you love.
        </p>
      </header>

      {/* Daily reflection / lyric */}
      {lyrics.length > 0 && (
        <section className="mb-12">
          <div className="bg-forest rounded-2xl p-8 md:p-10 text-center relative overflow-hidden">
            <div className="absolute inset-0 opacity-5">
              <svg viewBox="0 0 400 200" className="w-full h-full"><path d="M0 100 Q100 20 200 100 T400 100" stroke="white" strokeWidth="40" fill="none"/></svg>
            </div>
            <p className="text-cream/60 text-xs font-semibold uppercase tracking-widest mb-4">Today&apos;s Reflection</p>
            <blockquote className="font-serif text-cream text-xl md:text-2xl leading-relaxed italic mb-4">
              &ldquo;{lyrics[0].title}&rdquo;
            </blockquote>
            {lyrics[0].body && (
              <p className="text-cream/70 text-sm max-w-md mx-auto leading-relaxed">{lyrics[0].body}</p>
            )}
            {lyrics[0].source_name && (
              <p className="text-cream/40 text-xs mt-4">— {lyrics[0].source_name}</p>
            )}
          </div>
        </section>
      )}

      {/* Tips */}
      {tips.length > 0 && (
        <section className="mb-12">
          <h2 className="font-serif text-xl text-forest mb-5">Small things that help</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {tips.map((r) => <ResourceCard key={r.id} resource={r} />)}
          </div>
        </section>
      )}

      {/* Facts */}
      {facts.length > 0 && (
        <section className="mb-12">
          <h2 className="font-serif text-xl text-forest mb-5">Did you know?</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {facts.map((r) => <ResourceCard key={r.id} resource={r} />)}
          </div>
        </section>
      )}

      {/* External resources */}
      {links.length > 0 && (
        <section className="mb-12">
          <h2 className="font-serif text-xl text-forest mb-5">Organizations that help</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {links.map((r) => <ResourceCard key={r.id} resource={r} />)}
          </div>
        </section>
      )}

      {/* Be There CTA */}
      <section className="bg-amber/10 border border-amber/20 rounded-2xl p-8 text-center">
        <p className="text-2xl mb-3">🎓</p>
        <h2 className="font-serif text-xl text-forest mb-3">Be There Certificate</h2>
        <p className="text-earth/70 text-sm max-w-md mx-auto mb-5 leading-relaxed">
          The Busyhead Project offers a free online certification that helps you support the people
          in your life who are struggling. It takes about an hour and could change everything.
        </p>
        <a
          href="https://busyheadproject.org/bethere"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary inline-block"
        >
          Get certified →
        </a>
      </section>
    </div>
  );
}
