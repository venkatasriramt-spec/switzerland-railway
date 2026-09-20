import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
import json
import os

class ArtemisAdvancedEnv(gym.Env):
    """
    Advanced Multi-Agent RL Environment for the Swiss Railway Network.
    Incorporates static metadata and dynamic topological track data (edge hashes).
    """
    metadata = {"render_modes": ["console"]}

    def __init__(self, num_trains=None):
        super(ArtemisAdvancedEnv, self).__init__()
        
        self.num_trains_param = num_trains
        base_dir = os.path.dirname(__file__)
        data_dir = os.path.join(base_dir, "..", "data")
        
        # Load the pre-processed mini dataset (Solves RAM explosion)
        with open(os.path.join(data_dir, "mini_routes.json"), "r") as f:
            self.routes = json.load(f)
            
        # Load and process master dataset
        self.master_df = pd.read_csv(os.path.join(data_dir, "master_dataset.csv"))
        unique_trips = self.master_df['trip_id'].unique()
        self.num_trains = self.num_trains_param if self.num_trains_param is not None else len(unique_trips)
        self.train_trips = unique_trips[:self.num_trains]
        
        # Extract metadata per train
        self.train_metadata = []
        for trip_id in self.train_trips:
            trip_data = self.master_df[self.master_df['trip_id'] == trip_id].sort_values('stop_sequence')
            first_row = trip_data.iloc[0]
            
            max_speed_ms = float(first_row.get('max_speed_kmh', 140)) / 3.6
            weight = float(first_row.get('weight_tons', 150))
            carriages = float(first_row.get('carriages', 4))
            power = 1.0 if str(first_row.get('power_supply', 'electric')).lower() == 'electric' else 0.0
            gauge = float(first_row.get('gauge', 1435)) / 1435.0
            
            route_data = self.routes.get(trip_id, {})
            total_dist = route_data.get("total_distance_m", 100000.0)
            segments = route_data.get("segments", [])
            
            self.train_metadata.append({
                'trip_id': trip_id,
                'total_dist': total_dist,
                'segments': segments,
                'max_speed_ms': max_speed_ms,
                'weight': weight,
                'carriages': carriages,
                'power': power,
                'gauge': gauge
            })
        
        self.action_space = spaces.MultiDiscrete([3] * self.num_trains)
        self.obs_dim = 9
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, 
            shape=(self.num_trains, self.obs_dim), 
            dtype=np.float32
        )
        
        self.state = np.zeros((self.num_trains, 3), dtype=np.float32)
        self.dt = 10.0
        self.current_time = 0.0
        self.max_time = 86400.0
        
        # Curriculum Learning Weight
        self.collision_weight = 1.0

    def set_collision_weight(self, weight):
        """Called by CurriculumCallback to scale the penalty over time."""
        self.collision_weight = weight

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.state = np.zeros((self.num_trains, 3), dtype=np.float32)
        self.current_time = 0.0
        return self._get_obs(), {}

    def _get_obs(self):
        obs = np.zeros((self.num_trains, self.obs_dim), dtype=np.float32)
        
        # Topological Hash Mapping
        active_edges = {} # edge_id -> list of train_ids currently on this edge
        danger_zones = [] # list of (train_id, [edge_ids in next 200m])
        
        for i in range(self.num_trains):
            pos = self.state[i][0]
            segments = self.train_metadata[i]['segments']
            
            current_edge = None
            danger_edges = []
            accumulated = 0.0
            
            for seg in segments:
                edge_id = seg.get('edge_id')
                length = seg.get('length_m', 0.0)
                
                # Check if train is currently on this segment
                if accumulated <= pos < (accumulated + length):
                    current_edge = edge_id
                    
                # Check if this segment is in the next 200m (Danger Zone)
                if pos < (accumulated + length) <= (pos + 200.0) or (accumulated <= pos + 200.0 < accumulated + length):
                    danger_edges.append(edge_id)
                    
                accumulated += length
                if accumulated > pos + 200.0:
                    break # Optimization: stop parsing once past the danger zone
                    
            if current_edge is not None:
                if current_edge not in active_edges:
                    active_edges[current_edge] = []
                active_edges[current_edge].append(i)
                
            danger_zones.append(danger_edges)
            
        # Calculate topological distance to train ahead
        dist_ahead = np.full(self.num_trains, 10000.0)
        
        for i in range(self.num_trains):
            # Check for direct collision (multiple trains on exact same current edge)
            pos = self.state[i][0]
            current_edge = None
            if len(danger_zones[i]) > 0:
                # The first edge in danger zone is the current edge
                current_edge = danger_zones[i][0] 
                
            if current_edge in active_edges and len(active_edges[current_edge]) > 1:
                dist_ahead[i] = 0.0 # Collision!
            else:
                # Check for warnings (another train occupies any edge in my next 200m)
                for edge in danger_zones[i]:
                    if edge in active_edges:
                        # Ensure it's not just me on that edge
                        other_trains = [t for t in active_edges[edge] if t != i]
                        if len(other_trains) > 0:
                            dist_ahead[i] = 50.0 # Warning threshold
                            break
                            
        # Build observation vector
        for i in range(self.num_trains):
            pos, speed, delay = self.state[i]
            meta = self.train_metadata[i]
            obs[i] = [
                pos, 
                speed, 
                delay, 
                dist_ahead[i],
                meta['max_speed_ms'],
                meta['weight'],
                meta['carriages'],
                meta['power'],
                meta['gauge']
            ]
        return obs

    def step(self, action):
        rewards = np.zeros(self.num_trains, dtype=np.float32)
        obs = self._get_obs()
        
        for i in range(self.num_trains):
            pos, speed, delay = self.state[i]
            meta = self.train_metadata[i]
            dist_ahead = obs[i][3]
            
            weight_factor = 150.0 / max(1.0, meta['weight'])
            
            if action[i] == 0:   # Brake
                accel = -1.0 * weight_factor
            elif action[i] == 2: # Accelerate
                accel = 1.0 * weight_factor
            else:                # Coast
                accel = 0.0
                
            speed += accel * self.dt
            
            # A. Max Speed Enforcement
            if speed > meta['max_speed_ms']:
                rewards[i] -= 10.0
                speed = meta['max_speed_ms']
                
            if speed < 0: speed = 0.0
            
            # B. Collision Detection (Scaled by Curriculum Weight)
            if dist_ahead <= 0.0 and obs[i][0] > 0:
                rewards[i] -= (500.0 * self.collision_weight) # Collision!
                speed = 0.0 
            elif dist_ahead <= 50.0 and speed > 0:
                rewards[i] -= (50.0 * self.collision_weight) # Dangerously close!
                
            pos += speed * self.dt
            
            # C. Reaching Destination Logic
            if pos >= meta['total_dist']:
                pos = meta['total_dist']
                if speed == 0.0:
                    rewards[i] += 100.0
                else:
                    rewards[i] -= 20.0
                    speed = 0.0
            else:
                if speed > 0:
                    rewards[i] += 0.1
            
            self.state[i] = [pos, speed, delay]
                
        self.current_time += self.dt
        terminated = False
        truncated = self.current_time >= self.max_time
            
        total_reward = float(np.sum(rewards))
        return self._get_obs(), total_reward, terminated, truncated, {}
