import asyncio
import json
import os
import sys

# Ensure simulation package can be imported
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "simulation"))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from artemis_env import ArtemisEnv
from stable_baselines3 import PPO

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for the simulation state
env = None
model = None
simulation_task = None
connected_clients = []
latest_state = []

async def run_simulation():
    global env, model, latest_state
    print("Initializing RL Environment and Model for WebSocket streaming...")
    env = ArtemisEnv() # Defaults to 5643 trains now
    
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "models", "artemis_final_model.zip")
    # Load model without passing env, as the observation spaces won't match
    model = PPO.load(model_path)
    
    obs, info = env.reset()
    import numpy as np
    
    while True:
        # Step the environment
        action = np.zeros(env.num_trains, dtype=int)
        
        # Batch predict for the 100-train PPO model
        for i in range(0, env.num_trains, 100):
            batch_obs = obs[i:i+100]
            actual_len = len(batch_obs)
            if actual_len < 100:
                pad_width = 100 - actual_len
                batch_obs = np.pad(batch_obs, ((0, pad_width), (0, 0)), mode='constant')
                
            batch_action, _states = model.predict(batch_obs, deterministic=True)
            action[i:i+actual_len] = batch_action[:actual_len]
            
        obs, reward, done, truncated, info = env.step(action)
        
        # Get coordinates
        latest_state = env.get_train_coordinates()
        
        # Broadcast to all connected clients
        if connected_clients:
            payload = json.dumps({
                "time": env.current_time,
                "trains": latest_state
            })
            for client in connected_clients:
                try:
                    await client.send_text(payload)
                except:
                    pass
        
        # If the 24 hour period finished, reset
        if done or truncated:
            obs, info = env.reset()
            
        # Control the simulation speed (0.1s = 10 FPS)
        await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup_event():
    global simulation_task
    simulation_task = asyncio.create_task(run_simulation())

@app.get("/api/trains/metadata")
def get_train_metadata():
    if env is None or not hasattr(env, 'master_df'):
        return {"error": "Environment not initialized"}
    
    # Get unique trips with their static metadata
    metadata_df = env.master_df.drop_duplicates(subset=['trip_id']).copy()
    cols = ['trip_id', 'route_short_name', 'trip_headsign', 'carriages', 'max_speed_kmh', 'weight_tons']
    metadata_df = metadata_df[cols].fillna("")
    
    # Return as list of dictionaries
    records = metadata_df.to_dict(orient="records")
    return {"metadata": records}

@app.websocket("/ws/simulation")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            # Just keep the connection alive, we don't expect client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
