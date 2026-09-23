#!/bin/bash

# Ensure logs directory exists
mkdir -p logs
mkdir -p models
mkdir -p tensorboard_logs

echo "Starting Safety Monitor in the background..."
python monitor_safety.py &
SAFETY_PID=$!

echo "Starting Shared Memory Server (Redis Loader)..."
python scripts/shared_memory_server.py

echo "Geographically chunking dataset..."
python scripts/split_regions.py

echo "Launching 4 Regional Training Scripts (28 vCPUs total)..."
echo "Check the logs/ folder for detailed outputs of the background tasks."

# Run first 3 in background, redirecting standard output to their logs so they don't corrupt the terminal
python -u train_dispatcher.py --region Northeast > logs/Northeast_stdout.log 2>&1 &
PID1=$!

python -u train_dispatcher.py --region Northwest > logs/Northwest_stdout.log 2>&1 &
PID2=$!

python -u train_dispatcher.py --region Southeast > logs/Southeast_stdout.log 2>&1 &
PID3=$!

python -u train_dispatcher.py --region Southwest > logs/Southwest_stdout.log 2>&1 &
PID4=$!

# Run the master progress bar in the foreground to monitor all 4 processes via Redis
python scripts/master_progress_bar.py

# Wait for background jobs to finish
wait $PID1
wait $PID2
wait $PID3
wait $PID4

echo "All Regional Trainings Completed."
echo "Shutting down Safety Monitor..."
kill $SAFETY_PID
echo "Done."
