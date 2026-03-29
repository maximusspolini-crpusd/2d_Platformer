import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
import pygame


class PlatformerEnv(gym.Env):
    def __init__(self):
        super(PlatformerEnv, self).__init__()
    # ... rest of your init code ...
        
        # --- 1. THE CONTROLLER (ACTIONS) ---
        # 0: Idle, 1: Left, 2: Right, 3: Jump, 4: Jump Left, 5: Jump Right
        self.action_space = spaces.Discrete(6)
        
        # --- 2. THE EYES (OBSERVATION) ---
        # 5x5 grid = 25 numbers
        self.observation_space = spaces.Box(
            low=-1.0, high=2.0, shape=(121,), dtype=np.float32
        )
        
        # --- 3. PHYSICS VARIABLES ---
        self.player_x = 0
        self.player_y = 0
        self.y_velocity = 0.0
        self.is_grounded = False
        self.level_data = []

    def reset(self, seed=None):
        """Builds a new level and drops the player at Spawn."""
        super().reset(seed=seed)
        
        # (Replace this with your actual generation function later)
        # self.level_data = generate_perfect_climber(length=10) 
        
        # Dummy level for testing right now:
        self.level_data = [
            'PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP',
            'Pkkkk                                                 P',
            'Pkkkk                                                 P',
            'P                                                     P',
            'P                                                     P',
            'P                                                     P',
            'P                                                     P',
            'P                                                     P',
            'P                                                     P',
            'P                                                     P',
            'P                           P        PP      PP       P',
            'P                           P                         P',
            'P                           P                         P',
            'P  S                        P                         P',
            'PPPPPP       PPPP    PP     PKKKKKKKKKKKKKKKKKK       P',
            'PKKKKKKKKKKKKKKKKKKKKKKKKKKKPPPPPPPPPPPPPPPPPPP       P',
            'PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP       P',
            'P                                                     P',
            'P                                                     P',
            'P                                                     P',
            'P                                                     P',
            'P                                                     P',
            'G                                                     P',
            'G                                                     P',
            'G                                                     P',
            'G                                                     P',
            'PPPPP    PP     PP      PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP',
            'P                       P',
            'PKKKKKKKKKKKKKKKKKKKKKKKP',
            'PPPPPPPPPPPPPPPPPPPPPPPPP'

        ]
        
        # Find the 'S' to set spawn coordinates
        for r, row in enumerate(self.level_data):
            for c, char in enumerate(row):
                if char == 'S':
                    self.player_x = c
                    self.player_y = r
                    
        self.y_velocity = 0.0
        self.is_grounded = True
        
        return self._get_observation(), {}

    def step(self, action):
        """Runs one frame of the game."""
        
        # --- 1. X-AXIS MOVEMENT ---
        dx = 0
        if action in [1, 4]: # Left or Jump Left
            dx = -1
        elif action in [2, 5]: # Right or Jump Right
            dx = 1
            
        # Check X collisions
        new_x = self.player_x + dx
        if 0 <= new_x < len(self.level_data[0]): # Keep on screen horizontally
            
            # THE FIX: Check if the player is safely inside the vertical map bounds first!
            if 0 <= int(self.player_y) < len(self.level_data):
                if self.level_data[int(self.player_y)][int(new_x)] != 'P':
                    self.player_x = new_x # Move if not hitting a wall
            else:
                self.player_x = new_x # If they are above the map in the sky, let them move freely

        # --- 2. Y-AXIS MOVEMENT (GRAVITY & JUMPING) ---
        if action in [3, 4, 5] and self.is_grounded:
            self.y_velocity = -1.5 # Jump power (negative goes up)
            self.is_grounded = False
            
        # Apply Gravity
        self.y_velocity += 0.5 # Gravity pulls down
        if self.y_velocity > 1.5:  # Terminal velocity
            self.y_velocity = 1.5 
            
        new_y = self.player_y + self.y_velocity
        
        # Check Y collisions (Floor/Ceiling)
        if self.y_velocity > 0: # Falling Down
            # If the block below us is a Platform ('P')
            if int(new_y) < len(self.level_data) and self.level_data[int(new_y)][int(self.player_x)] == 'P':
                self.player_y = int(new_y) - 1 # Snap to top of platform
                self.y_velocity = 0
                self.is_grounded = True
            else:
                self.player_y = new_y
                self.is_grounded = False
        else: # Jumping Up
            self.player_y = new_y
            self.is_grounded = False

        # --- 3. REWARDS AND GAME OVER LOGIC ---
        reward = 0
        done = False
        
        # Reward for moving right!
        if dx > 0:
            reward += 1 
            
        # Penalize standing still
        if action == 0:
            reward -= 0.1 

        # Check what tile the player is currently inside
        current_tile = '.'
        if 0 <= int(self.player_y) < len(self.level_data):
            current_tile = self.level_data[int(self.player_y)][int(self.player_x)]

        # Did they hit spikes?
        if current_tile == 'K':
            reward -= 100 # Massive penalty
            done = True
            print("AI Died!")

        # Did they touch the Goal?
        elif current_tile == 'G':
            reward += 1000 # Massive reward
            done = True
            print("AI BEAT THE LEVEL!")

        # Turn on the visualizer!
        #self.render()
        
        return self._get_observation(), reward, done, False, {}

    def _get_observation(self):
        """Creates the 11x11 vision cone around the AI."""
        vision_radius = 5
        obs = []
        
        int_y = int(self.player_y)
        int_x = int(self.player_x)
        
        for r in range(int_y - vision_radius, int_y + vision_radius + 1):
            for c in range(int_x - vision_radius, int_x + vision_radius + 1):
                if r < 0 or r >= len(self.level_data) or c < 0 or c >= len(self.level_data[0]):
                    obs.append(1.0) # Out of bounds looks like a solid wall
                else:
                    tile = self.level_data[r][c]
                    if tile == 'P': obs.append(1.0)
                    elif tile == 'K': obs.append(-20.0)
                    elif tile == 'G': obs.append(20.0)
                    else: obs.append(-0.01) 
                        
        return np.array(obs, dtype=np.float32)
    def render(self):
        """Draws a simple Pygame window to watch the AI learn."""
        # Initialize Pygame only once
        if not hasattr(self, 'screen'):
            pygame.init()
            self.cell_size = 25 # Size of each block
            width = len(self.level_data[0]) * self.cell_size
            height = len(self.level_data) * self.cell_size
            self.screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption("AI Training Vision")
            self.clock = pygame.time.Clock()

        # Fill background with black
        self.screen.fill((0, 0, 0))

        # Draw the map
        for r, row in enumerate(self.level_data):
            for c, char in enumerate(row):
                rect = pygame.Rect(c * self.cell_size, r * self.cell_size, self.cell_size, self.cell_size)
                if char == 'P': 
                    pygame.draw.rect(self.screen, (100, 100, 100), rect) # Gray platforms
                elif char == 'K': 
                    pygame.draw.rect(self.screen, (255, 0, 0), rect)     # Red spikes
                elif char == 'G': 
                    pygame.draw.rect(self.screen, (0, 255, 0), rect)     # Green goal
                elif char == 'S': 
                    pygame.draw.rect(self.screen, (255, 255, 0), rect, 1) # Yellow outline for spawn

        # Draw the AI Player (Blue Square)
        player_rect = pygame.Rect(int(self.player_x) * self.cell_size, int(self.player_y) * self.cell_size, self.cell_size, self.cell_size)
        pygame.draw.rect(self.screen, (0, 150, 255), player_rect) 

        # Update the screen
        pygame.display.flip()
        
        # Lock the framerate so we can actually see it (otherwise it's a blur)
        # You can change this to 120 or 200 if you want it to train faster while watching!
        self.clock.tick(60) 
        
        # Keep the window from freezing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()