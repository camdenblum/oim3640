-- Seed all 32 NFL teams with accurate data
-- This runs if ESPN sync hasn't populated data yet

INSERT INTO teams (name, city, abbreviation, conference, division, home_stadium, primary_color, secondary_color)
VALUES
  ('Cardinals',    'Arizona',       'ARI', 'NFC', 'NFC West',  'State Farm Stadium',        '#97233F', '#FFB612'),
  ('Falcons',      'Atlanta',       'ATL', 'NFC', 'NFC South', 'Mercedes-Benz Stadium',     '#A71930', '#000000'),
  ('Ravens',       'Baltimore',     'BAL', 'AFC', 'AFC North', 'M&T Bank Stadium',          '#241773', '#000000'),
  ('Bills',        'Buffalo',       'BUF', 'AFC', 'AFC East',  'Highmark Stadium',          '#00338D', '#C60C30'),
  ('Panthers',     'Carolina',      'CAR', 'NFC', 'NFC South', 'Bank of America Stadium',   '#0085CA', '#101820'),
  ('Bears',        'Chicago',       'CHI', 'NFC', 'NFC North', 'Soldier Field',             '#0B162A', '#C83803'),
  ('Bengals',      'Cincinnati',    'CIN', 'AFC', 'AFC North', 'Paycor Stadium',            '#FB4F14', '#000000'),
  ('Browns',       'Cleveland',     'CLE', 'AFC', 'AFC North', 'Huntington Bank Field',     '#311D00', '#FF3C00'),
  ('Cowboys',      'Dallas',        'DAL', 'NFC', 'NFC East',  'AT&T Stadium',              '#003594', '#041E42'),
  ('Broncos',      'Denver',        'DEN', 'AFC', 'AFC West',  'Empower Field at Mile High','#FB4F14', '#002244'),
  ('Lions',        'Detroit',       'DET', 'NFC', 'NFC North', 'Ford Field',                '#0076B6', '#B0B7BC'),
  ('Packers',      'Green Bay',     'GB',  'NFC', 'NFC North', 'Lambeau Field',             '#203731', '#FFB612'),
  ('Texans',       'Houston',       'HOU', 'AFC', 'AFC South', 'NRG Stadium',               '#03202F', '#A71930'),
  ('Colts',        'Indianapolis',  'IND', 'AFC', 'AFC South', 'Lucas Oil Stadium',         '#002C5F', '#A2AAAD'),
  ('Jaguars',      'Jacksonville',  'JAX', 'AFC', 'AFC South', 'EverBank Stadium',          '#006778', '#D7A22A'),
  ('Chiefs',       'Kansas City',   'KC',  'AFC', 'AFC West',  'Arrowhead Stadium',         '#E31837', '#FFB81C'),
  ('Raiders',      'Las Vegas',     'LV',  'AFC', 'AFC West',  'Allegiant Stadium',         '#000000', '#A5ACAF'),
  ('Chargers',     'Los Angeles',   'LAC', 'AFC', 'AFC West',  'SoFi Stadium',              '#0080C6', '#FFC20E'),
  ('Rams',         'Los Angeles',   'LA',  'NFC', 'NFC West',  'SoFi Stadium',              '#003594', '#FFA300'),
  ('Dolphins',     'Miami',         'MIA', 'AFC', 'AFC East',  'Hard Rock Stadium',         '#008E97', '#FC4C02'),
  ('Vikings',      'Minnesota',     'MIN', 'NFC', 'NFC North', 'U.S. Bank Stadium',         '#4F2683', '#FFC62F'),
  ('Patriots',     'New England',   'NE',  'AFC', 'AFC East',  'Gillette Stadium',          '#002244', '#C60C30'),
  ('Saints',       'New Orleans',   'NO',  'NFC', 'NFC South', 'Caesars Superdome',         '#D3BC8D', '#101820'),
  ('Giants',       'New York',      'NYG', 'NFC', 'NFC East',  'MetLife Stadium',           '#0B2265', '#A71930'),
  ('Jets',         'New York',      'NYJ', 'AFC', 'AFC East',  'MetLife Stadium',           '#125740', '#000000'),
  ('Eagles',       'Philadelphia',  'PHI', 'NFC', 'NFC East',  'Lincoln Financial Field',   '#004C54', '#A5ACAF'),
  ('Steelers',     'Pittsburgh',    'PIT', 'AFC', 'AFC North', 'Acrisure Stadium',          '#FFB612', '#101820'),
  ('49ers',        'San Francisco', 'SF',  'NFC', 'NFC West',  'Levi''s Stadium',           '#AA0000', '#B3995D'),
  ('Seahawks',     'Seattle',       'SEA', 'NFC', 'NFC West',  'Lumen Field',               '#002244', '#69BE28'),
  ('Buccaneers',   'Tampa Bay',     'TB',  'NFC', 'NFC South', 'Raymond James Stadium',     '#D50A0A', '#FF7900'),
  ('Titans',       'Tennessee',     'TEN', 'AFC', 'AFC South', 'Nissan Stadium',            '#0C2340', '#4B92DB'),
  ('Commanders',   'Washington',    'WAS', 'NFC', 'NFC East',  'FedExField',                '#5A1414', '#FFB612')
ON CONFLICT (abbreviation) DO UPDATE SET
  name = EXCLUDED.name,
  home_stadium = EXCLUDED.home_stadium,
  primary_color = EXCLUDED.primary_color,
  secondary_color = EXCLUDED.secondary_color,
  updated_at = NOW();

-- Initialize Elo ratings for all teams
INSERT INTO elo_ratings (team_id, rating)
SELECT id, 1500 FROM teams
ON CONFLICT (team_id) DO NOTHING;
