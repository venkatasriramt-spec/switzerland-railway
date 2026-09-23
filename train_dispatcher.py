import argparse
import json
import os
import logging
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from simulation.dispatcher_env import DispatcherEnv

def make_env(region_name, region_trains):
    def _init():
        return DispatcherEnv(region_name=region_name, region_trains=region_trains)
    return _init

def main():
    parser = argparse.ArgumentParser(description="Train Regional Dispatcher AI")
    parser.add_argument("--region", type=str, required=True, help="Region to train (e.g. Northeast)")
    args = parser.parse_args()

    # Configure logging for this specific region
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        filename=f'logs/train_dispatcher_{args.region}.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logging.info(f"Starting training for Region: {args.region}")
    
    # Load region data
    try:
        with open("data/regions.json", "r") as f:
            regions_data = json.load(f)
            if args.region not in regions_data:
                raise ValueError(f"Region {args.region} not found in data/regions.json")
            region_trains = regions_data[args.region]
    except FileNotFoundError:
        logging.error("data/regions.json not found. Did you run split_regions.py?")
        exit(1)

    logging.info(f"Loaded {len(region_trains)} trains for {args.region}")
    
    # We use 7 parallel environments per region as per the implementation plan (4 regions * 7 = 28 cores)
    num_envs = 7 
    env = SubprocVecEnv([make_env(args.region, region_trains) for _ in range(num_envs)])
    
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=f"./tensorboard_logs/dispatcher_{args.region}/")
    
    logging.info("Commencing PPO training...")
    
    from stable_baselines3.common.callbacks import BaseCallback
    import redis

    class RedisProgressCallback(BaseCallback):
        def __init__(self, region, total_timesteps, verbose=0):
            super().__init__(verbose)
            self.region = region
            self.total_timesteps = total_timesteps
            self.r = redis.Redis(host='localhost', port=6379, db=0)

        def _on_step(self) -> bool:
            # Sync progress every 100 steps to avoid spamming Redis
            if self.num_timesteps % 100 == 0:
                self.r.set(f"progress:{self.region}", f"{self.num_timesteps}/{self.total_timesteps}")
            return True

    # Train for a small number of timesteps for demonstration
    total_steps = 50000
    callback = RedisProgressCallback(args.region, total_steps)
    model.learn(total_timesteps=total_steps, progress_bar=False, callback=callback)
    
    os.makedirs('models', exist_ok=True)
    save_path = f"models/dispatcher_{args.region}_final_model.zip"
    model.save(save_path)
    logging.info(f"Training complete. Saved model to {save_path}")

if __name__ == "__main__":
    main()
