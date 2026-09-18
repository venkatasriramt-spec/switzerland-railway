import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
import json

class ArtemisEnv(gym.Env):
    """
    A multi-agent reinforcement learning environment for the Swiss Railway Network.
    Controls the speed (accelerate, coast, brake) for all active trains.
    """
    metadata = {"render_modes": ["console"]}

    def __init__(self, num_trains=None):
        super(ArtemisEnv, self).__init__()
        
        print("Initializing ARTEMIS RL Environment...")
        
        self.num_trains_param = num_trains
        
        import os
        base_dir = os.path.dirname(__file__)
        data_dir = os.path.join(base_dir, "..", "data")
        
        # Load the precompiled routes for ultra-fast simulation
        print("Loading compiled routes from data/compiled_routes.json...")
        with open(os.path.join(data_dir, "compiled_routes.json"), "r") as f:
            self.routes = json.load(f)
            
        print("Loading master dataset from data/master_dataset.csv...")
        self.master_df = pd.read_csv(os.path.join(data_dir, "master_dataset.csv"))
        
        # Assign unique trip IDs
        unique_trips = self.master_df['trip_id'].unique()
        self.num_trains = self.num_trains_param if self.num_trains_param is not None else len(unique_trips)
        self.train_trips = unique_trips[:self.num_trains]
        
        # Action Space: 3 discrete actions (Brake, Coast, Accelerate) for each train
        self.action_space = spaces.MultiDiscrete([3] * self.num_trains)
        
        # Observation Space: Position, Speed, Delay for each train
        # [position_m, speed_ms, delay_s]
        self.observation_space = spaces.Box(
            low=0, 
            high=1000000, # Large arbitrary high
            shape=(self.num_trains, 3), 
            dtype=np.float32
        )
        
        # Precompute start and end coordinates for fast interpolation
        self.train_coords = []
        for trip_id in self.train_trips:
            trip_data = self.master_df[self.master_df['trip_id'] == trip_id].sort_values('stop_sequence')
            start_lat = trip_data.iloc[0]['stop_lat']
            start_lon = trip_data.iloc[0]['stop_lon']
            end_lat = trip_data.iloc[-1]['stop_lat']
            end_lon = trip_data.iloc[-1]['stop_lon']
            
            # Get total distance from compiled routes
            total_dist = self.routes.get(trip_id, {}).get("total_distance_m", 100000.0) # default to 100km if missing
            
            self.train_coords.append({
                'trip_id': trip_id,
                'start_lat': start_lat, 'start_lon': start_lon,
                'end_lat': end_lat, 'end_lon': end_lon,
                'total_dist': total_dist
            })
        
        # Initialize train states
        self.state = np.zeros((self.num_trains, 3), dtype=np.float32)
        
        # Simulation step size (10 seconds)
        self.dt = 10.0
        self.current_time = 0.0
        self.max_time = 86400.0 # 24 hours in seconds

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # Reset all trains to start position (0), speed (0), and zero delay
        self.state = np.zeros((self.num_trains, 3), dtype=np.float32)
        self.current_time = 0.0
        
        return self.state, {}

    def step(self, action):
        """
        Takes an action for each train.
        0 = Brake (decelerate by 1 m/s^2)
        1 = Coast (maintain speed)
        2 = Accelerate (accelerate by 1 m/s^2)
        """
        rewards = np.zeros(self.num_trains, dtype=np.float32)
        
        for i in range(self.num_trains):
            pos, speed, delay = self.state[i]
            
            # Apply action (acceleration)
            if action[i] == 0:   # Brake
                accel = -1.0
            elif action[i] == 2: # Accelerate
                accel = 1.0
            else:                # Coast
                accel = 0.0
                
            # Update speed (v = u + at)
            speed += accel * self.dt
            speed = max(0.0, min(speed, 40.0)) # Cap speed between 0 and 40 m/s (144 km/h)
            
            # Update position (s = ut + 0.5at^2)
            # Simplification: ds = v * dt
            pos += speed * self.dt
            
            # Update state
            self.state[i] = [pos, speed, delay]
            
            # Simple reward: promote moving forward, penalize braking or stopping
            if speed > 0:
                rewards[i] += 0.1
            if action[i] == 0:
                rewards[i] -= 0.05
                
        self.current_time += self.dt
        
        # Check termination (24 hours passed)
        terminated = False
        truncated = False
        if self.current_time >= self.max_time:
            truncated = True
            
        # Combine all train rewards into a single scalar for PPO
        total_reward = float(np.sum(rewards))
        
        return self.state, total_reward, terminated, truncated, {}
        
    def render(self):
        print(f"Time: {self.current_time}s | State Sample: {self.state[0]}")
        
    def get_train_coordinates(self):
        """
        Returns a list of dictionaries containing the interpolated GPS coordinates
        and telemetry for every train to be used by the web dashboard.
        """
        trains_data = []
        for i in range(self.num_trains):
            pos, speed, delay = self.state[i]
            coords = self.train_coords[i]
            
            # Calculate completion percentage (0.0 to 1.0)
            progress = min(1.0, pos / coords['total_dist'])
            
            # Linear interpolation for latitude and longitude
            current_lat = coords['start_lat'] + progress * (coords['end_lat'] - coords['start_lat'])
            current_lon = coords['start_lon'] + progress * (coords['end_lon'] - coords['start_lon'])
            
            trains_data.append({
                "id": i,
                "trip_id": coords['trip_id'],
                "lat": current_lat,
                "lon": current_lon,
                "speed": float(speed),
                "delay": float(delay)
            })
            
        return trains_data

