#!/bin/bash
trap 'echo "Exiting, killing server"; kill 0' EXIT

# Start Qdrant
sudo docker start qdrant

# Activate environment
source .venv/bin/activate

# Run evaluation before starting server (optional)
if [ "$1" = "--with-eval" ]; then
    echo "Running RAG evaluation..."
    python -m evaluation.run_evaluation
fi

# Start services
uvicorn server:app --reload &
cd app 
npm run dev &

wait
