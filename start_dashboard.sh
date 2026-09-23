#!/bin/bash

echo "Cleaning up old processes..."
fuser -k 8000/tcp 2>/dev/null
fuser -k 5173/tcp 2>/dev/null

echo "Starting ARTEMIS Backend (FastAPI)..."
cd dashboard/backend
# Start the backend server in the background
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting ARTEMIS Frontend (React/Vite)..."
cd ../frontend
# Start the frontend server in the foreground
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!

echo "Both servers are running!"
echo "Dashboard is available at: http://localhost:5173"
echo "Press [CTRL+C] to stop both servers."

# Wait for user interrupt
trap "echo 'Shutting down servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
