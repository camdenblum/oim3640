'use client';
import { useState } from 'react';
import { X, Phone } from 'lucide-react';

export default function CrisisBanner() {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed) return null;

  return (
    <div
      role="banner"
      className="bg-forest/95 text-cream text-sm py-2.5 px-4 flex items-center justify-between gap-3 sticky top-0 z-50"
    >
      <div className="flex items-center gap-2 flex-wrap">
        <Phone className="w-4 h-4 shrink-0 text-cream/70" aria-hidden />
        <span className="text-cream/80">Need immediate support?</span>
        <span className="text-cream/60">You are not alone.</span>
        <a
          href="tel:988"
          className="font-semibold text-amber underline underline-offset-2 hover:no-underline"
        >
          Call or text 988
        </a>
        <span className="text-cream/40 hidden sm:inline">·</span>
        <a
          href="sms:741741?body=HOME"
          className="font-semibold text-amber underline underline-offset-2 hover:no-underline hidden sm:inline"
        >
          Text HOME to 741741
        </a>
      </div>
      <button
        onClick={() => setDismissed(true)}
        aria-label="Dismiss crisis banner"
        className="text-cream/50 hover:text-cream transition-colors shrink-0"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
