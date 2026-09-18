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

    def __init__(self):
        super(ArtemisEnv, self).__init__()
        
        print("Initializing ARTEMIS RL Environment...")
        
        # We will limit to the first 100 trains for now to speed up training,
        # but this can easily scale to all 5643 trains.
        self.num_trains = 100
        
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
        
        import os
        base_dir = os.path.dirname(__file__)
        data_dir = os.path.join(base_dir, "..", "data")
        
        # Load the precompiled routes for ultra-fast simulation
        print("Loading compiled routes from data/compiled_routes.json...")
        with open(os.path.join(data_dir, "compiled_routes.json"), "r") as f:
            self.routes = json.load(f)
            
        print("Loading master dataset from data/master_dataset.csv...")
        self.master_df = pd.read_csv(os.path.join(data_dir, "master_dataset.csv"))
        
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
            speed = max(0.0, speed) # Prevent reversing
            
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

