import os
import sys

# Ensure the parent directory is in the path if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from artemis_env import ArtemisEnv
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy

def main():
    print("Loading ARTEMIS RL Environment...")
    env = ArtemisEnv()
    
    model_path = "./models/artemis_final_model.zip"
    if not os.path.exists(model_path):
        print(f"Error: Could not find model at {model_path}")
        print("Please ensure the training script has finished.")
        return
        
    print(f"Loading trained model from {model_path}...")
    model = PPO.load(model_path, env=env)
    
    print("Evaluating policy over 3 episodes...")
    # Evaluate the policy deterministically
    mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=3, deterministic=True)
    print(f"Evaluation complete! Mean Reward: {mean_reward:.2f} +/- {std_reward:.2f}")
    
    print("\nStarting visual run-through...")
    obs, info = env.reset()
    
    # Run a single episode to completion
    total_reward = 0
    done = False
    truncated = False
    steps = 0
    
    while not (done or truncated):
        # Predict the optimal action using the trained neural network (deterministic=True)
        action, _states = model.predict(obs, deterministic=True)
        
        # Advance the environment by 1 timestep
        obs, reward, done, truncated, info = env.step(action)
        
        total_reward += reward
        steps += 1
        
        if steps % 100 == 0:
            print(f"Timestep {steps} | Cumulative Reward: {total_reward:.2f}")

    print("\n--- Episode Finished ---")
    print(f"Total Steps Survived: {steps}")
    print(f"Final Total Reward: {total_reward:.2f}")
    
if __name__ == '__main__':
    main()
