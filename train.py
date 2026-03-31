from stable_baselines3 import PPO
from platformer_env import PlatformerEnv
import os

from stable_baselines3.common.callbacks import BaseCallback
import numpy as np

class ProgressLoggingCallback(BaseCallback):
    def __init__(self, verbose=0):
        super(ProgressLoggingCallback, self).__init__(verbose)
        self.checkpoints = []
        self.progresses = []

    def _on_step(self) -> bool:
        # SB3 puts the 'info' dictionary from your step() function into self.locals['infos']
        for info in self.locals.get("infos", []):
            if "checkpoint_reached" in info:
                self.checkpoints.append(info["checkpoint_reached"])
            if "level_progress" in info:
                self.progresses.append(info["level_progress"])
        
        return True

    def _on_rollout_end(self) -> None:
        # At the end of a batch, calculate the average and send it to TensorBoard!
        if len(self.checkpoints) > 0:
            avg_checkpoint = np.mean(self.checkpoints)
            avg_progress = np.mean(self.progresses)
            
            self.logger.record("Progress/Avg_Checkpoint_Reached", avg_checkpoint)
            self.logger.record("Progress/Avg_Level_Percent", avg_progress)
            
            # Print to console so you can see it working
            print(f"--- Rollout End | Avg Progress: {avg_progress:.1f}% | Avg Checkpoints: {avg_checkpoint:.1f} ---")
            
            # Clear the lists for the next batch
            self.checkpoints = []
            self.progresses = []

# 1. Boot up the invisible matrix version of your game
env = PlatformerEnv()

from stable_baselines3.common.callbacks import CheckpointCallback

# --- 10 HOUR SETTINGS ---
FPS_ESTIMATE = 680
HOURS = 1.5
TOTAL_STEPS = HOURS * 60 * 60 * FPS_ESTIMATE 
SAVE_FREQ = 500000 # Save every 500k steps (approx every 15-20 mins)
progress_logger = ProgressLoggingCallback()
# 1. Create the Checkpoint Manager
# This saves the brain to a folder called 'logs' automatically
checkpoint_callback = CheckpointCallback(
    save_freq=SAVE_FREQ, 
    save_path="./logs/",
    name_prefix="ai_marathon_checkpoint"
)

OLD_BRAIN_FILE = "brain3.zip" # Change to the name of your best save!
NEW_BRAIN_FILE = "brain4.zip"

if os.path.exists(OLD_BRAIN_FILE):
    print(f"Previous brain '{OLD_BRAIN_FILE}' found! Booting it up...")
    model = PPO.load(OLD_BRAIN_FILE, env=env)
else:
    print("No previous brain found. Creating a brand new brain...")
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./ai_learning_graphs/", learning_rate=0.0003)

model.learn(total_timesteps=100000, callback=progress_logger, progress_bar=False)

model.save(NEW_BRAIN_FILE)
print(f"💾 Success! Upgraded brain saved as: {NEW_BRAIN_FILE}")