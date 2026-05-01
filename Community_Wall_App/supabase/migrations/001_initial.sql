-- ─── Extensions ──────────────────────────────────────────────────────────────
create extension if not exists "uuid-ossp";

-- ─── Profiles ─────────────────────────────────────────────────────────────────
create table public.profiles (
  id                        uuid references auth.users on delete cascade primary key,
  username                  text unique,
  display_name              text,
  avatar_icon               text default 'mountain',
  healing_points            integer default 0,
  opt_out_leaderboard       boolean default false,
  trigger_warnings_enabled  boolean default false,
  login_streak              integer default 0,
  last_login_date           date,
  profile_completed         boolean default false,
  created_at                timestamptz default now(),
  updated_at                timestamptz default now()
);

alter table public.profiles enable row level security;

create policy "Users can read all profiles" on public.profiles
  for select using (true);
create policy "Users can update their own profile" on public.profiles
  for update using (auth.uid() = id);
create policy "Users can insert their own profile" on public.profiles
  for insert with check (auth.uid() = id);

-- ─── Prompts ──────────────────────────────────────────────────────────────────
create table public.prompts (
  id            uuid default gen_random_uuid() primary key,
  text          text not null,
  is_active     boolean default true,
  week_start    date,
  week_end      date,
  display_order integer default 0,
  created_at    timestamptz default now()
);

alter table public.prompts enable row level security;
create policy "Anyone can read active prompts" on public.prompts
  for select using (is_active = true);

-- ─── Responses ────────────────────────────────────────────────────────────────
create table public.responses (
  id                uuid default gen_random_uuid() primary key,
  user_id           uuid references public.profiles(id) on delete cascade,
  prompt_id         uuid references public.prompts(id) on delete cascade,
  content           text not null,
  display_name      text default 'a voice from the community',
  is_approved       boolean default false,
  is_flagged        boolean default false,
  moderation_score  float,
  created_at        timestamptz default now(),
  unique(user_id, prompt_id)
);

alter table public.responses enable row level security;
create policy "Anyone can read approved responses" on public.responses
  for select using (is_approved = true and is_flagged = false);
create policy "Users can insert own responses" on public.responses
  for insert with check (auth.uid() = user_id);
create policy "Users can read own responses" on public.responses
  for select using (auth.uid() = user_id);

-- ─── Reactions ────────────────────────────────────────────────────────────────
create table public.reactions (
  id            uuid default gen_random_uuid() primary key,
  user_id       uuid references public.profiles(id) on delete cascade,
  response_id   uuid references public.responses(id) on delete cascade,
  reaction_type text not null check (reaction_type in ('leaf', 'heart', 'lightbulb', 'mountain')),
  created_at    timestamptz default now(),
  unique(user_id, response_id, reaction_type)
);

alter table public.reactions enable row level security;
create policy "Anyone can read reactions" on public.reactions
  for select using (true);
create policy "Authenticated users can react" on public.reactions
  for insert with check (auth.uid() = user_id);
create policy "Users can remove own reactions" on public.reactions
  for delete using (auth.uid() = user_id);

-- ─── HP Transactions ──────────────────────────────────────────────────────────
create table public.hp_transactions (
  id          uuid default gen_random_uuid() primary key,
  user_id     uuid references public.profiles(id) on delete cascade,
  amount      integer not null,
  reason_code text not null,
  description text,
  created_at  timestamptz default now()
);

alter table public.hp_transactions enable row level security;
create policy "Users can read own HP transactions" on public.hp_transactions
  for select using (auth.uid() = user_id);
create policy "Service role can insert HP transactions" on public.hp_transactions
  for insert with check (true);

-- ─── Badges ───────────────────────────────────────────────────────────────────
create table public.badges (
  id              uuid default gen_random_uuid() primary key,
  slug            text unique not null,
  name            text not null,
  description     text,
  icon            text,
  condition_type  text,
  condition_value integer
);

create table public.user_badges (
  id         uuid default gen_random_uuid() primary key,
  user_id    uuid references public.profiles(id) on delete cascade,
  badge_id   uuid references public.badges(id) on delete cascade,
  earned_at  timestamptz default now(),
  unique(user_id, badge_id)
);

alter table public.badges enable row level security;
alter table public.user_badges enable row level security;
create policy "Anyone can read badges" on public.badges for select using (true);
create policy "Users can read own user_badges" on public.user_badges
  for select using (auth.uid() = user_id);

-- ─── Daily Check-ins ──────────────────────────────────────────────────────────
create table public.daily_checkins (
  id                  uuid default gen_random_uuid() primary key,
  user_id             uuid references public.profiles(id) on delete cascade,
  mood_score          integer not null check (mood_score between 1 and 5),
  journal_text        text,
  completed_breathing boolean default false,
  check_in_date       date default current_date,
  created_at          timestamptz default now(),
  unique(user_id, check_in_date)
);

alter table public.daily_checkins enable row level security;
create policy "Users can read own check-ins" on public.daily_checkins
  for select using (auth.uid() = user_id);
create policy "Users can insert own check-ins" on public.daily_checkins
  for insert with check (auth.uid() = user_id);

-- ─── Resources ────────────────────────────────────────────────────────────────
create table public.resources (
  id           uuid default gen_random_uuid() primary key,
  title        text not null,
  body         text,
  category     text check (category in ('tip', 'resource', 'fact', 'reflection', 'lyric')),
  source_name  text,
  source_url   text,
  is_active    boolean default true,
  created_at   timestamptz default now()
);

alter table public.resources enable row level security;
create policy "Anyone can read active resources" on public.resources
  for select using (is_active = true);

create table public.saved_resources (
  id          uuid default gen_random_uuid() primary key,
  user_id     uuid references public.profiles(id) on delete cascade,
  resource_id uuid references public.resources(id) on delete cascade,
  created_at  timestamptz default now(),
  unique(user_id, resource_id)
);

alter table public.saved_resources enable row level security;
create policy "Users can manage own saved resources" on public.saved_resources
  for all using (auth.uid() = user_id);

-- ─── Store ────────────────────────────────────────────────────────────────────
create table public.store_items (
  id          uuid default gen_random_uuid() primary key,
  name        text not null,
  description text,
  hp_cost     integer not null,
  category    text check (category in ('digital', 'giveaway', 'discount', 'wall')),
  is_available boolean default true,
  stock_count integer,
  created_at  timestamptz default now()
);

create table public.redemptions (
  id        uuid default gen_random_uuid() primary key,
  user_id   uuid references public.profiles(id) on delete cascade,
  item_id   uuid references public.store_items(id),
  hp_spent  integer not null,
  status    text default 'pending' check (status in ('pending', 'fulfilled', 'cancelled')),
  created_at timestamptz default now()
);

alter table public.store_items enable row level security;
alter table public.redemptions enable row level security;
create policy "Anyone can read store items" on public.store_items for select using (is_available = true);
create policy "Users can read own redemptions" on public.redemptions for select using (auth.uid() = user_id);
create policy "Users can insert own redemptions" on public.redemptions for insert with check (auth.uid() = user_id);

-- ─── Referrals ────────────────────────────────────────────────────────────────
create table public.referrals (
  id          uuid default gen_random_uuid() primary key,
  referrer_id uuid references public.profiles(id) on delete cascade,
  referred_id uuid references public.profiles(id) on delete cascade,
  created_at  timestamptz default now(),
  unique(referred_id)
);

-- ─── Functions ────────────────────────────────────────────────────────────────

-- Auto-create profile on sign up
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, display_name)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'name', split_part(new.email, '@', 1))
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Add HP and log transaction atomically
create or replace function public.add_hp(
  p_user_id     uuid,
  p_amount      integer,
  p_reason_code text,
  p_description text default null
) returns void language plpgsql security definer as $$
begin
  update public.profiles set healing_points = healing_points + p_amount where id = p_user_id;
  insert into public.hp_transactions (user_id, amount, reason_code, description)
  values (p_user_id, p_amount, p_reason_code, p_description);
end;
$$;

-- Reaction counts helper view
create or replace view public.response_reaction_counts as
  select
    response_id,
    count(*) filter (where reaction_type = 'leaf')       as leaf_count,
    count(*) filter (where reaction_type = 'heart')      as heart_count,
    count(*) filter (where reaction_type = 'lightbulb')  as lightbulb_count,
    count(*) filter (where reaction_type = 'mountain')   as mountain_count
  from public.reactions
  group by response_id;

-- Leaderboard view (opt-in only)
create or replace view public.leaderboard as
  select id, display_name, avatar_icon, healing_points
  from public.profiles
  where opt_out_leaderboard = false
  order by healing_points desc
  limit 50;

-- Enable realtime on responses and reactions
alter publication supabase_realtime add table public.responses;
alter publication supabase_realtime add table public.reactions;
