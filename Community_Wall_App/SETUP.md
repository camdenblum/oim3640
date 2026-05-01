# The Busyhead Wall — Setup Guide

## Prerequisites
- Node.js 18+
- A [Supabase](https://supabase.com) account (free tier works)
- Optional: OpenAI API key (for content moderation)

## 1. Install dependencies
```bash
cd Community_Wall_App
npm install
```

## 2. Create a Supabase project
1. Go to [supabase.com](https://supabase.com) → New Project
2. Copy your **Project URL** and **anon key** from Settings → API

## 3. Set up environment variables
```bash
cp .env.example .env.local
```
Fill in `.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key   # Settings → API → service_role
OPENAI_API_KEY=sk-...                              # Optional — for moderation
NEXT_PUBLIC_SITE_URL=http://localhost:3000
ADMIN_EMAILS=your@email.com                       # Comma-separated admin emails
```

## 4. Run database migrations
In your Supabase project → SQL Editor, run:
1. `supabase/migrations/001_initial.sql`
2. `supabase/seed.sql`

Or use the Supabase CLI:
```bash
npx supabase db push
npx supabase db seed
```

## 5. Configure Supabase Auth
In Supabase → Authentication → Providers:
- Enable **Email** (magic links)
- Enable **Google** OAuth (optional but recommended)

In Authentication → URL Configuration:
- Site URL: `http://localhost:3000` (or your production domain)
- Redirect URLs: Add `http://localhost:3000/api/auth/callback`

## 6. Run the development server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000)

## 7. Moderate responses
**By default, all responses are held for manual approval** unless OpenAI moderation passes them automatically.

Visit `/admin` (must be logged in with an email in `ADMIN_EMAILS`) to:
- Approve or remove pending cards
- Review flagged content
- See community analytics

## Deploy to Vercel
```bash
npx vercel
```
Set all environment variables in Vercel dashboard under Project → Settings → Environment Variables.
Update your Supabase Auth redirect URL to your production domain.

## HP System Summary
| Action | HP |
|--------|-----|
| First response ever | +100 |
| Submit a response | +50 |
| Daily login | +10 |
| React to a card (max 20/day) | +5 each |
| Daily check-in | +25 |
| Complete profile | +30 |
| Referral | +75 |

HP cannot be purchased — earned only.
