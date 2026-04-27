#!/bin/bash

set -e  # stop if anything fails

echo "==> Creating virtual environment..."
python3 -m venv .venv

echo "==> Activating virtual environment..."
source .venv/bin/activate

echo "==> Installing requirements..."
pip install -r requirements.txt

echo "==> Running backend setup..."
uvicorn api:app --reload

echo "==> Running frontend setup..."
cd frontend
npm run dev

echo ""
echo "✅ Setup complete! Run 'source .venv/bin/activate' to activate the env."