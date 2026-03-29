from stable_baselines3 import PPO
from platformer_env import PlatformerEnv

# 1. Boot up the invisible matrix version of your game
env = PlatformerEnv()

# 2. Give the AI a brain (PPO is the best algorithm for 2D platformers)
model = PPO("MlpPolicy", env, verbose=1)

# 3. Let it play the game 50,000 times! (This will take a few minutes)
print("Starting training... Go grab a snack!")
model.learn(total_timesteps=50000)

# 4. Save the trained brain to a file
model.save("smart_platformer_bot")
print("Training complete! Brain saved.")