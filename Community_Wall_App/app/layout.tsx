import type { Metadata, Viewport } from 'next';
import './globals.css';
import Navigation from '@/components/Navigation';
import CrisisBanner from '@/components/CrisisBanner';
import { createClient } from '@/lib/supabase/server';

export const metadata: Metadata = {
  title: 'The Busyhead Wall — The Busyhead Project',
  description:
    'A safe, stigma-free community space for honest conversations about mental health. Add your voice to the wall.',
  openGraph: {
    title: 'The Busyhead Wall',
    description: 'A digital Community Wall for The Busyhead Project — ending the stigma, one conversation at a time.',
    siteName: 'The Busyhead Project',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#2D5016',
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  let profile = null;
  if (user) {
    const { data } = await supabase
      .from('profiles')
      .select('display_name, avatar_icon, healing_points')
      .eq('id', user.id)
      .single();
    profile = data;
  }

  return (
    <html lang="en">
      <body>
        <CrisisBanner />
        <Navigation user={user} profile={profile} />
        <main className="min-h-screen pb-24">{children}</main>
        <footer className="bg-forest text-cream/80 py-10 px-6 mt-16">
          <div className="max-w-5xl mx-auto">
            <svg viewBox="0 0 800 60" className="w-full mb-6 treeline opacity-30" aria-hidden>
              <path d="M0 60 L20 20 L40 60 M30 60 L60 10 L90 60 M75 60 L110 5 L145 60
                       M130 60 L170 15 L210 60 M195 60 L240 8 L285 60 M270 60 L320 12 L370 60
                       M355 60 L405 6 L455 60 M440 60 L490 14 L540 60 M525 60 L575 9 L625 60
                       M610 60 L660 11 L710 60 M695 60 L740 4 L785 60 L800 60 L800 60 L0 60Z" />
            </svg>
            <div className="grid md:grid-cols-3 gap-8 text-sm">
              <div>
                <h3 className="font-serif text-cream text-lg mb-2">The Busyhead Project</h3>
                <p className="text-cream/60 text-xs leading-relaxed">
                  A 501(c)(3) non-profit mental health foundation dedicated to ending the stigma,
                  one conversation at a time.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-cream/90 mb-2">Resources</h3>
                <ul className="space-y-1 text-cream/60">
                  <li><a href="https://busyheadproject.org/resources" className="hover:text-cream transition-colors" target="_blank" rel="noopener noreferrer">busyheadproject.org</a></li>
                  <li><a href="tel:988" className="hover:text-cream transition-colors">988 Suicide & Crisis Lifeline</a></li>
                  <li><a href="sms:741741" className="hover:text-cream transition-colors">Crisis Text Line — Text HOME to 741741</a></li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-cream/90 mb-2">Support the Mission</h3>
                <a
                  href="https://givebutter.com/thebusyheadproject"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block bg-amber text-white text-xs font-semibold px-4 py-2 rounded-full hover:bg-amber-light transition-colors"
                >
                  Donate ↗
                </a>
                <p className="text-cream/40 text-xs mt-3">
                  &copy; {new Date().getFullYear()} The Busyhead Project.
                </p>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
