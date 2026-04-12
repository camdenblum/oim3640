{
  "name": "nfl-predictor-proxy",
  "version": "1.0.0",
  "description": "Proxy server for NFL Predictor app — live odds, schedule, scores, AI predictions",
  "type": "module",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "node --watch server.js"
  },
  "dependencies": {
    "cors": "^2.8.5",
    "dotenv": "^16.4.5",
    "express": "^4.18.2",
    "node-cron": "^3.0.3",
    "node-fetch": "^3.3.2",
    "ws": "^8.17.0"
  }
}

