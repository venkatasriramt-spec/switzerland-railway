import os
import sys
import threading
import time
import psutil

# Ensure the parent directory is in the path if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from artemis_env import ArtemisEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback

def memory_monitor():
    """Background thread to kill the process if RAM hits 90%"""
    while True:
        mem = psutil.virtual_memory()
        if mem.percent > 90.0:
            print(f"CRITICAL: Memory usage hit {mem.percent}%. Terminating to prevent OOM crash!")
            os._exit(1)
        time.sleep(2)

def make_env():
    def _init():
        env = ArtemisEnv()
        return env
    return _init

if __name__ == '__main__':
    print("Setting up Vectorized Environment...")
    
    # Start RAM monitor
    monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
    monitor_thread.start()
    
    # Use 24 cores to maximize efficiency without causing OOM
    num_cpu = 24
    
    # We use DummyVecEnv for 1 cpu to avoid multiprocessing overhead if testing,
    # but for training we want all 16 cores.
    vec_env = SubprocVecEnv([make_env() for _ in range(num_cpu)])
    
    print(f"Setting up PPO Agent across {num_cpu} cores...")
    
    import glob
    # Find the latest checkpoint to resume from
    checkpoints = glob.glob('./models/checkpoints/*.zip')
    if checkpoints:
        latest_checkpoint = max(checkpoints, key=os.path.getmtime)
        print(f"Resuming training from checkpoint: {latest_checkpoint}")
        model = PPO.load(latest_checkpoint, env=vec_env, tensorboard_log="./models/tb_logs/")
    else:
        print("Starting fresh PPO model...")
        model = PPO("MlpPolicy", vec_env, verbose=1, tensorboard_log="./models/tb_logs/")
    
    # Save a checkpoint every 100,000 steps (per environment, so 100k / 16)
    # We set save_freq to 6250 (6250 * 16 = 100,000)
    checkpoint_callback = CheckpointCallback(
        save_freq=6250,
        save_path='./models/checkpoints/',
        name_prefix='artemis_model'
    )
    
    print("Starting full model training for 10,000,000 timesteps...")
    model.learn(total_timesteps=10000000, callback=checkpoint_callback)
    
    print("Training complete! Saving final model...")
    model.save("./models/artemis_final_model")
    
    # Cleanup
    vec_env.close()
