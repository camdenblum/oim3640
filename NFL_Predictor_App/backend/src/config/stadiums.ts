export interface StadiumInfo {
  lat: number;
  lon: number;
  dome: boolean;
}

export const STADIUM_COORDS: Record<string, StadiumInfo> = {
  'Arrowhead Stadium':          { lat: 39.0489, lon: -94.4839, dome: false },
  'Highmark Stadium':           { lat: 42.7738, lon: -78.7870, dome: false },
  'Empower Field at Mile High': { lat: 39.7439, lon: -105.0201, dome: false },
  'Gillette Stadium':           { lat: 42.0909, lon: -71.2643, dome: false },
  'M&T Bank Stadium':           { lat: 39.2780, lon: -76.6227, dome: false },
  'Paycor Stadium':             { lat: 39.0955, lon: -84.5160, dome: false },
  'Cleveland Browns Stadium':   { lat: 41.5061, lon: -81.6995, dome: false },
  'AT&T Stadium':               { lat: 32.7480, lon: -97.0928, dome: true },
  'Ford Field':                 { lat: 42.3400, lon: -83.0456, dome: true },
  'Lambeau Field':              { lat: 44.5013, lon: -88.0622, dome: false },
  'U.S. Bank Stadium':          { lat: 44.9736, lon: -93.2575, dome: true },
  'Caesars Superdome':          { lat: 29.9511, lon: -90.0812, dome: true },
  'MetLife Stadium':            { lat: 40.8135, lon: -74.0744, dome: false },
  'Lincoln Financial Field':    { lat: 39.9008, lon: -75.1675, dome: false },
  'Acrisure Stadium':           { lat: 40.4468, lon: -80.0158, dome: false },
  "Levi's Stadium":             { lat: 37.4033, lon: -121.9694, dome: false },
  'Lumen Field':                { lat: 47.5952, lon: -122.3316, dome: false },
  'Raymond James Stadium':      { lat: 27.9759, lon: -82.5033, dome: false },
  'NRG Stadium':                { lat: 29.6847, lon: -95.4107, dome: true },
  'Lucas Oil Stadium':          { lat: 39.7601, lon: -86.1639, dome: true },
  'TIAA Bank Field':            { lat: 30.3239, lon: -81.6373, dome: false },
  'Hard Rock Stadium':          { lat: 25.9580, lon: -80.2389, dome: false },
  'Nissan Stadium':             { lat: 36.1665, lon: -86.7713, dome: false },
  'Bank of America Stadium':    { lat: 35.2258, lon: -80.8528, dome: false },
  'Mercedes-Benz Stadium':      { lat: 33.7554, lon: -84.4010, dome: true },
  'FedExField':                 { lat: 38.9078, lon: -76.8645, dome: false },
  'Soldier Field':              { lat: 41.8623, lon: -87.6167, dome: false },
  'Allegiant Stadium':          { lat: 36.0909, lon: -115.1833, dome: true },
  'SoFi Stadium':               { lat: 33.9535, lon: -118.3392, dome: true },
  'State Farm Stadium':         { lat: 33.5276, lon: -112.2626, dome: true },
  'EverBank Stadium':           { lat: 30.3239, lon: -81.6373, dome: false },
  'Huntington Bank Field':      { lat: 41.5061, lon: -81.6995, dome: false },
};
