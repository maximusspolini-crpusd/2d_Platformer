from stable_baselines3 import PPO
from platformer_env import PlatformerEnv

# 1. Boot up the invisible matrix version of your game
env = PlatformerEnv()

# 2. Give the AI a brain (PPO is the best algorithm for 2D platformers)
model = PPO("MlpPolicy", env, learning_rate=0.00007, verbose=1)

from stable_baselines3.common.callbacks import CheckpointCallback

# --- 10 HOUR SETTINGS ---
FPS_ESTIMATE = 500
HOURS = 10
TOTAL_STEPS = HOURS * 60 * 60 * FPS_ESTIMATE 
SAVE_FREQ = 500000 # Save every 500k steps (approx every 15-20 mins)

# 1. Create the Checkpoint Manager
# This saves the brain to a folder called 'logs' automatically
checkpoint_callback = CheckpointCallback(
    save_freq=SAVE_FREQ, 
    save_path="./logs/",
    name_prefix="ai_marathon_checkpoint"
)

# 2. Initialize Model (Optimized for 10-hour marathon)
model = PPO(
    "MlpPolicy", 
    env, 
    learning_rate=0.0001,  # Gentle learning for long runs
    verbose=1
)

print(f"🚀 DARK TRAINING STARTED")
print(f"💾 Saving checkpoints to ./logs/ every {SAVE_FREQ:,} steps")

# 3. Start the Grind
try:
    model.learn(
        total_timesteps=TOTAL_STEPS, 
        callback=checkpoint_callback,
        progress_bar=True
    )
except KeyboardInterrupt:
    print("\n⚠️ Manually stopped. Saving current progress...")

# 4. Final Master Save
model.save("god_tier_ai_final")
print("✅ MARATHON COMPLETE. Final brain: god_tier_ai_final.zip")