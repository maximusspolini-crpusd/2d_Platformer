import pygame
from platformer_env import PlatformerEnv

def main():
    # 1. Boot up your custom environment
    env = PlatformerEnv()
    obs, info = env.reset()
    
    # 2. Start the game loop
    running = True
    while running:
        # Draw the screen
        env.render()
        
        # 3. Read human keyboard inputs
        keys = pygame.key.get_pressed()
        
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        jump = keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]
        
        # 4. Translate keys into AI Action Space (0-5)
        action = 0 # Default to Idle
        
        if jump and left:
            action = 4
        elif jump and right:
            action = 5
        elif jump:
            action = 3
        elif left:
            action = 1
        elif right:
            action = 2
            
        # 5. Step the environment forward exactly one frame
        obs, reward, done, truncated, info = env.step(action)
        
        # Print rewards so you can see what the AI "feels"
        if reward != 0 and reward != -0.05: # Ignoring the tiny jump sweat penalty for cleaner logs
            print(f"Reward gained/lost: {reward}")
            
        # 6. Reset if we die or win
        if done or truncated:
            print("--- GAME OVER! RESETTING ---")
            obs, info = env.reset()

        # Catch the X button on the window to quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()

if __name__ == "__main__":
    main()