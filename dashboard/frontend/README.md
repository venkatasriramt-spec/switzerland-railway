# ARTEMIS Switzerland — Web Dashboard Frontend

This directory contains the React + Vite frontend for the ARTEMIS Switzerland real-time railway simulation dashboard.

The application connects to the FastAPI backend via WebSockets to receive live updates of the train kinematics (latitude, longitude, speed, and delay) as determined by the trained PPO reinforcement learning agent.

## Features
- **Live Interactive Map:** Displays trains dynamically moving across the Swiss rail network in real-time.
- **WebSocket Streaming:** Connects to `ws://localhost:8000/ws/simulation` to receive sub-second updates from the physics engine.

## Getting Started

### Prerequisites
Make sure you have Node.js installed. Then, install dependencies:
```bash
npm install
```

### Running the Development Server
Before starting the frontend, ensure the FastAPI backend is running on port 8000.

Start the Vite development server:
```bash
npm run dev
```

Open the local URL (usually `http://localhost:5173`) in your browser to view the live dashboard.
