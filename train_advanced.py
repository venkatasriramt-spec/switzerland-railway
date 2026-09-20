import os
import multiprocessing
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, CallbackList
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.logger import configure

# Import the new advanced environment and callbacks
from simulation.artemis_env_advanced import ArtemisAdvancedEnv
from simulation.callbacks import CurriculumCallback, FileProgressCallback

def make_env(rank, num_trains_to_train, seed=0):
    """
    Utility function for multiprocessed env.
    """
    def _init():
        env = ArtemisAdvancedEnv(num_trains=num_trains_to_train)
        env.reset(seed=seed + rank)
        return env
    return _init

def main():
    # We can train on a subset of trains for speed, e.g., 500 trains.
    num_trains_to_train = 500 
    
    # Detect the number of available CPU cores
    # We leave 4 cores free so the VM hypervisor and OS remain completely responsive.
    total_cores = multiprocessing.cpu_count()
    num_cpu = max(1, total_cores - 4) 
    
    # Wrap it in a SubprocVecEnv to utilize all CPU cores and RAM
    vec_env = SubprocVecEnv([make_env(i, num_trains_to_train) for i in range(num_cpu)])
    
    checkpoint_dir = './models/checkpoints_advanced/'
    latest_model_path = None
    
    if os.path.exists(checkpoint_dir):
        import glob
        checkpoints = glob.glob(os.path.join(checkpoint_dir, '*.zip'))
        if checkpoints:
            latest_model_path = max(checkpoints, key=os.path.getmtime)
            
    if latest_model_path:
        model = PPO.load(latest_model_path, env=vec_env, tensorboard_log="./tensorboard_logs/advanced_model/")
    else:
        # Initialize PPO with MlpPolicy
        model = PPO(
            "MlpPolicy", 
            vec_env, 
            verbose=1,
            learning_rate=0.0003,
            n_steps=2048,
            batch_size=64 * num_cpu, # Scale batch size with number of parallel envs
            n_epochs=10,
            gamma=0.99, # Discount factor
            tensorboard_log="./tensorboard_logs/advanced_model/"
        )
    
    # Create models directory if it doesn't exist
    os.makedirs("models", exist_ok=True)
    
    # Save a checkpoint every 10,000 steps
    checkpoint_callback = CheckpointCallback(
        save_freq=max(10000 // num_cpu, 1), # Adjust frequency based on parallel envs
        save_path='./models/checkpoints_advanced/',
        name_prefix='artemis_adv_model'
    )
    
    # Curriculum Learning Callback
    total_timesteps = 1_000_000
    curriculum_callback = CurriculumCallback(total_timesteps=total_timesteps)
    
    # File Progress Callback
    os.makedirs("logs", exist_ok=True)
    progress_callback = FileProgressCallback(total_timesteps=total_timesteps)
    
    # Combine callbacks
    callbacks = CallbackList([checkpoint_callback, curriculum_callback, progress_callback])
    
    # Configure logger to write training metrics to files ONLY (no stdout spam)
    new_logger = configure("./logs", ["log", "csv"])
    model.set_logger(new_logger)
    
    # Train the agent with a beautiful progress bar in the terminal
    model.learn(total_timesteps=total_timesteps, callback=callbacks, progress_bar=True)
    
    model.save("models/artemis_advanced_final_model")

if __name__ == "__main__":
    main()
