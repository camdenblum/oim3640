'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useState } from 'react';
import { Menu, X, LogOut, User } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';
import type { User as SupabaseUser } from '@supabase/supabase-js';

interface Profile {
  display_name: string | null;
  avatar_icon: string;
  healing_points: number;
}

interface Props {
  user: SupabaseUser | null;
  profile: Profile | null;
}

const NAV_LINKS = [
  { href: '/',         label: 'The Wall' },
  { href: '/learn',    label: 'Learn' },
  { href: '/checkin',  label: 'Daily Moment' },
  { href: '/store',    label: 'Merch Tent' },
];

export default function Navigation({ user, profile }: Props) {
  const pathname = usePathname();
  const router = useRouter();
  const supabase = createClient();
  const [menuOpen, setMenuOpen] = useState(false);

  async function signOut() {
    await supabase.auth.signOut();
    router.push('/');
    router.refresh();
  }

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' : pathname.startsWith(href);

  return (
    <nav className="bg-cream/95 backdrop-blur-sm border-b border-earth/10 sticky top-[44px] z-40" role="navigation" aria-label="Main">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <span className="text-2xl" aria-hidden>🌲</span>
          <div className="hidden sm:block">
            <p className="font-serif font-semibold text-forest leading-tight text-sm">The Busyhead</p>
            <p className="font-serif text-forest/60 leading-tight text-xs">Community Wall</p>
          </div>
          <div className="sm:hidden font-serif font-semibold text-forest text-sm">Busyhead Wall</div>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                isActive(href)
                  ? 'bg-forest/10 text-forest'
                  : 'text-earth/70 hover:text-forest hover:bg-forest/5'
              }`}
            >
              {label}
            </Link>
          ))}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          {user && profile ? (
            <>
              <span className="hp-chip text-xs hidden sm:inline-flex" aria-label={`${profile.healing_points} Healing Points`}>
                🌿 {profile.healing_points.toLocaleString()}
              </span>
              <Link
                href="/profile"
                className="flex items-center gap-2 hover:opacity-80 transition-opacity"
                aria-label="Your profile"
              >
                <span className="w-8 h-8 rounded-full bg-forest/10 flex items-center justify-center text-sm" aria-hidden>
                  {profile.display_name?.charAt(0).toUpperCase() ?? '?'}
                </span>
              </Link>
              <button
                onClick={signOut}
                aria-label="Sign out"
                className="btn-ghost text-earth/50 hover:text-earth p-2"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </>
          ) : (
            <Link href="/auth" className="btn-primary text-sm py-2 px-4">
              Join the wall
            </Link>
          )}

          {/* Mobile menu */}
          <button
            className="md:hidden btn-ghost p-2"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={menuOpen}
          >
            {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile nav */}
      {menuOpen && (
        <div className="md:hidden border-t border-earth/10 bg-cream/98 px-4 py-3 space-y-1">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setMenuOpen(false)}
              className={`block px-4 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                isActive(href)
                  ? 'bg-forest/10 text-forest'
                  : 'text-earth/70 hover:text-forest'
              }`}
            >
              {label}
            </Link>
          ))}
          {user && (
            <>
              <Link href="/profile" onClick={() => setMenuOpen(false)} className="flex items-center gap-2 px-4 py-2.5 text-sm text-earth/70">
                <User className="w-4 h-4" /> Profile
              </Link>
              {profile && (
                <div className="px-4 py-2">
                  <span className="hp-chip text-xs">🌿 {profile.healing_points.toLocaleString()} HP</span>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </nav>
  );
}
