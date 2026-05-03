# Deploying The Busyhead Wall

The app is a Node.js + Express server (server.js) backed by SQLite.
It serves index.html as the frontend and provides a REST API for shared data.

---

## Run locally right now

```bash
cd Community_Wall_App
npm start
```

Open http://localhost:3000 — cards are shared between all users on that machine.

---

## Deploy to Railway (recommended — free tier, persistent disk)

1. Go to https://railway.app and sign up with GitHub
2. Click **New Project → Deploy from GitHub repo**
3. Select `camdenblum/oim3640`
4. Set the **Root Directory** to `Community_Wall_App`
5. Railway auto-detects `railway.toml` — click **Deploy**
6. Go to **Settings → Variables** and add:
   ```
   SESSION_SECRET = some-long-random-string-here
   NODE_ENV       = production
   ```
7. Go to **Settings → Networking → Generate Domain** — your app is live

> Railway free tier: 500 hours/month, 1 GB disk. Enough for a real project.

---

## Deploy to Render (alternative — free tier, spins down when idle)

1. Go to https://render.com and sign up with GitHub
2. Click **New → Web Service**
3. Connect `camdenblum/oim3640`
4. Set:
   - **Root Directory:** `Community_Wall_App`
   - **Build Command:** `npm install`
   - **Start Command:** `node server.js`
5. Add environment variable: `SESSION_SECRET = some-long-random-string`
6. Click **Create Web Service**

> Note: Render free tier spins down after 15 min of inactivity. First load takes ~30s to wake.
> Railway is better for a live app that people actually use.

---

## Deploy to Fly.io (best performance, always-on free tier)

```bash
npm install -g flyctl
cd Community_Wall_App
fly launch        # follow prompts, choose the free tier
fly secrets set SESSION_SECRET="some-long-random-string"
fly deploy
```

---

## What's shared vs personal

| Data | Storage | Shared? |
|------|---------|---------|
| Wall cards | SQLite database | ✅ Yes — everyone sees the same wall |
| Reactions | SQLite database | ✅ Yes |
| User accounts | SQLite database | ✅ Yes — login works across devices |
| Daily login HP | SQLite database | ✅ Yes |
| Dog companion | localStorage | ❌ Device-only (personal/private) |
| Mood check-ins | localStorage | ❌ Device-only (private by design) |
| Badges / HP | localStorage | ❌ Device-only for now |

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SESSION_SECRET` | Yes | Long random string for session signing. Generate with: `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"` |
| `NODE_ENV` | No | Set to `production` in deployment |
| `PORT` | No | Defaults to 3000 |

---

## GitHub Pages (HTML-only, no shared data)

For a quick shareable link where each user gets their own isolated wall:

1. Go to github.com/camdenblum/oim3640
2. Settings → Pages → Source: Deploy from branch
3. Branch: `main`, Folder: `/Community_Wall_App`
4. Your URL: `https://camdenblum.github.io/oim3640/Community_Wall_App/`

Cards and reactions will be local to each device (localStorage mode).
Good for demos; use Railway/Render for a real shared community wall.
