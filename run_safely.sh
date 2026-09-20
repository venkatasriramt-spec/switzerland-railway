#!/bin/bash

echo "Checking dataset..."
if [ ! -f "data/mini_routes.json" ]; then
    echo "mini_routes.json not found! Running data pre-processor..."
    python scripts/preprocess_data.py
else
    echo "mini_routes.json already exists! Skipping pre-processing."
fi

echo "Starting Safety Monitor in the background..."
python monitor_safety.py &
MONITOR_PID=$!

echo "Starting Advanced AI Training..."
python -u train_advanced.py

echo "Training process ended. Shutting down Safety Monitor..."
kill $MONITOR_PID
echo "Done."
