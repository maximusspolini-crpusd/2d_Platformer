import time
from stable_baselines3 import PPO
from platformer_env import PlatformerEnv

# 1. Open the visible game environment
# Tell the environment to turn the Pygame window on!
env = PlatformerEnv(render_mode="human")
# 2. Load the brain
model = PPO.load("ai_brain.zip") # Or your specific checkpoint name

print("🍿 Grabbing popcorn... Watch the AI play!")

# --- THE FIX IS HERE ---
# Tell Python to split the two returned items into separate variables
obs, info = env.reset() 

while True:
    # The AI looks at the 'obs' and decides what to do
    action, _states = model.predict(obs, deterministic=True)
    
    # Step the environment forward
    # Modern Gymnasium returns 5 separate values, so we unpack all 5!
    obs, reward, terminated, truncated, info = env.step(action)
    
    # Draw the screen
    env.render()
    time.sleep(1/60)
    
    # If the player dies (terminated) or runs out of time (truncated)
    if terminated or truncated:
        obs, info = env.reset() # Don't forget to unpack here too!