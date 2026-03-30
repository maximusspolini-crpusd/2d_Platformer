from stable_baselines3 import PPO
from platformer_env import PlatformerEnv
import os

# 1. Boot up the invisible matrix version of your game
env = PlatformerEnv()

from stable_baselines3.common.callbacks import CheckpointCallback

# --- 10 HOUR SETTINGS ---
FPS_ESTIMATE = 600
HOURS = 8
TOTAL_STEPS = HOURS * 60 * 60 * FPS_ESTIMATE 
SAVE_FREQ = 500000 # Save every 500k steps (approx every 15-20 mins)

# 1. Create the Checkpoint Manager
# This saves the brain to a folder called 'logs' automatically
checkpoint_callback = CheckpointCallback(
    save_freq=SAVE_FREQ, 
    save_path="./logs/",
    name_prefix="ai_marathon_checkpoint"
)

OLD_BRAIN_FILE = "brain.zip" # Change to the name of your best save!
NEW_BRAIN_FILE = "brain.zip"

if os.path.exists(OLD_BRAIN_FILE):
    print(f"🧠 Veteran brain '{OLD_BRAIN_FILE}' found! Booting it up...")
    model = PPO.load(OLD_BRAIN_FILE, env=env)
else:
    print("🌱 No previous brain found. Birthing a brand new AI...")
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./ai_learning_graphs/", learning_rate=0.0003, ent_coef=0.1)

print("🚀 Launching Dark Training...")
model.learn(total_timesteps=TOTAL_STEPS, callback=checkpoint_callback, progress_bar=False)

model.save(NEW_BRAIN_FILE)
print(f"💾 Success! Upgraded brain saved as: {NEW_BRAIN_FILE}")