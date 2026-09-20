import numpy as np
import datetime
from stable_baselines3.common.callbacks import BaseCallback

class CurriculumCallback(BaseCallback):
    """
    Gradually increases the collision penalty weight as training progresses.
    Phase 1: 0% - 30% progress -> weight = 0.0 (Learn to move and stop)
    Phase 2: 30% - 70% progress -> weight scales linearly 0.0 to 1.0 (Learn to brake)
    Phase 3: 70% - 100% progress -> weight = 1.0 (Strict safety)
    """
    def __init__(self, total_timesteps: int, verbose=0):
        super(CurriculumCallback, self).__init__(verbose)
        self.total_timesteps = total_timesteps

    def _on_step(self) -> bool:
        # Calculate training progress (0.0 to 1.0)
        progress = self.num_timesteps / self.total_timesteps
        
        # Calculate current weight
        if progress < 0.3:
            weight = 0.0
        elif progress < 0.7:
            # Scale linearly from 0.0 at 30% to 1.0 at 70%
            weight = (progress - 0.3) / 0.4
        else:
            weight = 1.0
            
        # Update the environments via the SubprocVecEnv interface
        # env_method calls the method on all parallel environments
        self.training_env.env_method('set_collision_weight', weight)
        
        # Log to TensorBoard
        self.logger.record("curriculum/collision_weight", weight)
        
        return True

class FileProgressCallback(BaseCallback):
    """
    Writes clean training progress to a log file periodically (every 1%).
    """
    def __init__(self, total_timesteps, log_file="logs/training_progress.log", verbose=0):
        super(FileProgressCallback, self).__init__(verbose)
        self.total_timesteps = total_timesteps
        self.log_file = log_file
        self.last_percent = -1

    def _on_step(self) -> bool:
        progress = (self.num_timesteps / self.total_timesteps) * 100
        current_percent = int(progress)
        
        if current_percent > self.last_percent:
            self.last_percent = current_percent
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Build a simple ASCII progress bar
            filled = current_percent // 5
            bar = "#" * filled + "-" * (20 - filled)
            msg = f"[{timestamp}] Training Progress: [{bar}] {current_percent}% ({self.num_timesteps}/{self.total_timesteps} steps)\n"
            
            with open(self.log_file, "a") as f:
                f.write(msg)
                
        return True
