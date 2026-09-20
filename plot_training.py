import pandas as pd
import matplotlib.pyplot as plt
import os

# Load progress
df = pd.read_csv('logs/progress.csv')

# Create figure
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# Plot 1: Curriculum Weight
ax1.plot(df['time/total_timesteps'], df['curriculum/collision_weight'], 'b-', linewidth=2)
ax1.set_ylabel('Collision Penalty Weight', color='b')
ax1.tick_params(axis='y', labelcolor='b')
ax1.set_title('ARTEMIS Advanced AI Training Curriculum (1 Million Steps)')
ax1.grid(True)

# Plot 2: Policy Gradient Loss
ax2.plot(df['time/total_timesteps'], df['train/policy_gradient_loss'], 'r-', linewidth=2)
ax2.set_ylabel('Policy Gradient Loss', color='r')
ax2.tick_params(axis='y', labelcolor='r')
ax2.set_xlabel('Total Timesteps')
ax2.grid(True)

plt.tight_layout()
plt.savefig('/home/venkatasriramt/.gemini/antigravity-ide/brain/542bf617-8c35-4d73-8af9-41eebdc50db0/curriculum_training.png', dpi=150)
print("Saved plot to artifacts.")
