#!/bin/bash
# Quick-start script for local development (without Docker)
# Requirements: Node 20+, Python 3.11+, PostgreSQL 15+, Redis

set -e
echo "=== NFL Predictor App — Local Dev Start ==="

# Copy env if not already done
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — add your API keys before running predictions"
fi

# Install backend deps
echo "\n[1/4] Installing backend dependencies..."
cd backend && npm install && cd ..

# Install frontend deps
echo "\n[2/4] Installing frontend dependencies..."
cd frontend && npm install && cd ..

# Install Python deps
echo "\n[3/4] Installing Python analytics dependencies..."
cd analytics && pip install -r requirements.txt && cd ..

# Seed the database
echo "\n[4/4] Seeding database with historical NFL data..."
python database/seeds/seed.py

echo "\n=== Starting services ==="
echo "Backend  → http://localhost:3001"
echo "Frontend → http://localhost:3000"
echo "Analytics→ http://localhost:8001"
echo ""

# Start all services in parallel
trap 'kill 0' EXIT

cd backend && npm run dev &
cd analytics && uvicorn api:app --host 0.0.0.0 --port 8001 --reload &
cd frontend && npm run dev &

wait
