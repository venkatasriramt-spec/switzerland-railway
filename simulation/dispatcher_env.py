import gymnasium as gym
from gymnasium import spaces
import numpy as np
import redis
import json
import logging

# Configure logging
logging.basicConfig(
    filename='logs/dispatcher_env.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DispatcherEnv(gym.Env):
    def __init__(self, region_name="Northeast", region_trains=None):
        super(DispatcherEnv, self).__init__()
        
        self.region_name = region_name
        self.region_trains = region_trains or []
        self.num_trains = len(self.region_trains)
        
        if self.num_trains == 0:
            # Fallback for testing
            self.num_trains = 100
            
        logging.info(f"Initialized DispatcherEnv for region {region_name} with {self.num_trains} trains")
        
        # Action space: 0 = Hold, 1 = Dispatch for each train
        self.action_space = spaces.MultiBinary(self.num_trains)
        
        # Observation space: Delay for each train (normalized)
        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=(self.num_trains,), dtype=np.float32
        )
        
        self.current_step = 0
        self.max_steps = 288 # 5-minute steps in a 24-hour day
        self.delays = np.zeros(self.num_trains, dtype=np.float32)
        
        # Connect to shared memory (Redis)
        try:
            self.redis = redis.Redis(host='localhost', port=6379, db=0)
            self.redis.ping()
        except BaseException as e:
            logging.error(f"Redis connection failed: {e}")
            self.redis = None

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.delays = np.zeros(self.num_trains, dtype=np.float32)
        return self.delays, {}

    def step(self, action):
        self.current_step += 1
        
        # Internally, the Dispatcher's action (Dispatch or Hold) interacts with the Low-Level Driver.
        # For this Macro-Step, holding a train increases its delay penalty.
        # Dispatching it might cause a delay if the network is congested.
        
        network_congestion = np.sum(action) / self.num_trains
        
        rewards = np.zeros(self.num_trains)
        for i in range(self.num_trains):
            if action[i] == 0:
                # Hold: Increases delay safely
                self.delays[i] += 0.05
                rewards[i] -= 1.0 # Small penalty for holding
            else:
                # Dispatch: Progresses train, but risks congestion delay
                if network_congestion > 0.5:
                    self.delays[i] += 0.1 * network_congestion
                    rewards[i] -= 5.0 # Large penalty for dispatching into massive congestion
                else:
                    self.delays[i] = max(0, self.delays[i] - 0.1)
                    rewards[i] += 10.0 # Reward for safely progressing
                    
        total_reward = np.sum(rewards)
        
        done = self.current_step >= self.max_steps
        truncated = False
        
        return self.delays, float(total_reward), done, truncated, {}
