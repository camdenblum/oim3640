-- ─── Prompts ──────────────────────────────────────────────────────────────────
insert into public.prompts (text, display_order, is_active, week_start, week_end) values
  ('One thing I wish people understood about my mental health is...', 1, true, current_date, current_date + 7),
  ('Something that has helped me in my darkest moments is...', 2, true, current_date, current_date + 7),
  ('A message I would leave for someone who feels completely alone right now...', 3, true, current_date, current_date + 7),
  ('Something I am still learning to forgive myself for...', 4, true, current_date, current_date + 7),
  ('The thing that keeps me going, even on the hardest days, is...', 5, true, current_date, current_date + 7);

-- ─── Badges ───────────────────────────────────────────────────────────────────
insert into public.badges (slug, name, description, icon, condition_type, condition_value) values
  ('first_step',           'From The Woods',             'Submitted your first response to the Wall.',         '🌲', 'first_response',  1),
  ('stick_season',         'Stick Season Survivor',      'Logged in 7 days in a row.',                        '🍂', 'login_streak',    7),
  ('we_all_be_here',       'We''ll All Be Here Forever', 'Reacted to 100 cards on the Wall.',                 '🤍', 'reactions_given', 100),
  ('northern_attitude',    'Northern Attitude',           'Reached 500 Healing Points.',                       '🏔️', 'hp_milestone',   500),
  ('busyhead',             'Busyhead',                    'Responded to all 5 prompts in one cycle.',           '🌿', 'full_cycle',      5),
  ('the_village',          'The Village',                 'Referred 3 friends to The Busyhead Wall.',          '🏡', 'referrals',       3),
  ('profile_complete',     'Fully Present',               'Completed your profile.',                           '✨', 'profile',         1),
  ('hp_1000',              'Lantern in the Dark',         'Reached 1,000 Healing Points.',                     '🕯️', 'hp_milestone',  1000);

-- ─── Mental Health Resources ──────────────────────────────────────────────────
insert into public.resources (title, body, category, source_name, source_url) values
  ('You are not a burden',
   'One of the most common thoughts in hard moments is that reaching out will burden the people you love. But the people who love you would rather carry some of your weight than watch you carry all of it alone. You are allowed to lean.',
   'tip', 'The Busyhead Project', 'https://busyheadproject.org/resources'),

  ('The 5-4-3-2-1 grounding technique',
   'When anxiety feels overwhelming, try this: name 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, 1 you can taste. It pulls your mind gently back into your body.',
   'tip', null, null),

  ('Did you know? 1 in 5 adults in the US experiences a mental illness in any given year',
   'Mental health conditions are among the most common health conditions in the world. You are not alone. You are not unusual. You are human.',
   'fact', 'NAMI', 'https://nami.org'),

  ('Crisis Text Line',
   'If you are in crisis or need to talk, text HOME to 741741. A trained crisis counselor is there for you, 24/7, completely free and confidential.',
   'resource', 'Crisis Text Line', 'https://crisistextline.org'),

  ('988 Suicide & Crisis Lifeline',
   'Call or text 988 anytime. You do not have to be suicidal to call — the lifeline is there for anyone in emotional distress. You are worth the call.',
   'resource', '988 Lifeline', 'https://988lifeline.org'),

  ('"It''s okay to be in a place of hurting."',
   '"We must all strive for the place of healing, forgiveness, awareness." — Noah Kahan. Reflection: What is one small step toward healing you could take today, even if it is just getting out of bed?',
   'lyric', 'Noah Kahan / The Busyhead Project', 'https://busyheadproject.org'),

  ('JED Foundation Resources',
   'The JED Foundation protects emotional health and prevents suicide for teens and young adults. Their site has guides for helping yourself and others.',
   'resource', 'JED Foundation', 'https://jedfoundation.org'),

  ('Hope For The Day',
   'HFTD is a proactive suicide prevention and mental health education non-profit. Their materials are honest, approachable, and stigma-free.',
   'resource', 'Hope For The Day', 'https://hftd.org'),

  ('Jack.org — For Young Canadians',
   'Jack.org trains and empowers young people across Canada to revolutionize how mental health is talked about in their communities.',
   'resource', 'Jack.org', 'https://jack.org'),

  ('Sleep and mental health are deeply connected',
   'Poor sleep worsens anxiety, depression, and emotional regulation. Even small improvements — a consistent bedtime, no screens 30 minutes before bed — can meaningfully shift how you feel.',
   'fact', null, null),

  ('The "Be There" Certificate',
   'The Busyhead Project offers a free online certification to help you support the people in your life who are struggling. It takes about an hour and could change everything for someone you love.',
   'resource', 'The Busyhead Project', 'https://busyheadproject.org/bethere'),

  ('"I''ll be okay"',
   '"I''ll be okay, not today, but I''ll be okay." — Noah Kahan. Reflection: You do not have to be healed today. You just have to be here today.',
   'lyric', 'Noah Kahan', null),

  ('Didi Hirsch Mental Health Services',
   'Providing compassionate mental health, substance use disorder treatment and suicide prevention services since 1942. Serving communities across Los Angeles and Orange County.',
   'resource', 'Didi Hirsch', 'https://didihirsch.org');

-- ─── Store Items ──────────────────────────────────────────────────────────────
insert into public.store_items (name, description, hp_cost, category, is_available) values
  ('Busyhead Digital Wallpaper — Vermont Mountains',
   'Exclusive phone wallpaper featuring a hand-illustrated Vermont mountainscape. 4K resolution for iPhone and Android.',
   150, 'digital', true),

  ('Busyhead Digital Wallpaper — The Wall',
   'A collage-style digital wallpaper inspired by the physical Community Wall, featuring notecard illustrations.',
   150, 'digital', true),

  ('Monthly Giveaway — Signed Vinyl',
   'One entry into this month''s draw for a vinyl record signed by Noah Kahan. Winners announced the last Friday of each month.',
   300, 'giveaway', true),

  ('Monthly Giveaway — Show Tickets',
   'One entry into the draw for a pair of show tickets to an upcoming Noah Kahan tour date near you.',
   500, 'giveaway', true),

  ('Monthly Giveaway — Meet & Greet',
   'One entry into the grand draw for a meet & greet experience with Noah at an upcoming show.',
   750, 'giveaway', true),

  ('Busyhead Project Merch Discount — 15% off',
   'A unique discount code for 15% off your next order at the official Busyhead Project merch store. Valid 30 days.',
   200, 'discount', true),

  ('Permanent Card on the Digital Wall',
   'Your name (or display name) will be pinned permanently at the top of the Community Wall. A lasting mark of your voice in this community.',
   1000, 'wall', true);
