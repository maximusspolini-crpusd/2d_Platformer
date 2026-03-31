import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
import math

# --- MATCHING PHYSICS CONSTANTS FROM MAIN.PY ---
TILE_SIZE = 30
GRAVITY = 0.8
JUMP_STRENGTH = -17

# --- 1. THE PLAYER CLASS (Copied from main.py) ---
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.vel_y = 0
        self.vel_x = 0
        self.on_ground = False
        self.max_speed = 5
        self.ground_friction = 0.7
        self.air_friction = 0.8
        self.coyote_timer = 0
        self.coyote_max = 10 

    def reset_position(self, start_x, start_y):
        self.vel_x = 0
        self.vel_y = 0
        self.rect.x = start_x
        self.rect.y = start_y

    def update(self, platforms, long_platforms, hazards, ihazards, goal, moving_left=False, moving_right=False, jumping=False):
        # Horizontal
        if moving_left: self.vel_x -= 1.0
        if moving_right: self.vel_x += 1.0
        
        if not moving_left and not moving_right:
            self.vel_x *= self.ground_friction if self.on_ground else self.air_friction

        self.vel_x = max(-self.max_speed, min(self.max_speed, self.vel_x))
        if abs(self.vel_x) < 0.1: self.vel_x = 0

        self.rect.x += self.vel_x
        for p in platforms + long_platforms:
            if self.rect.colliderect(p):
                if self.vel_x > 0: self.rect.right = p.left
                elif self.vel_x < 0: self.rect.left = p.right
                self.vel_x = 0

        # Vertical
        if jumping and self.coyote_timer > 0:
            self.vel_y = JUMP_STRENGTH
            self.coyote_timer = 0
            self.on_ground = False

        self.vel_y += GRAVITY
        self.vel_y = min(15, self.vel_y)
        self.rect.y += self.vel_y
        self.on_ground = False

        for p in platforms + long_platforms:
            if self.rect.colliderect(p):
                if self.vel_y > 0:
                    self.rect.bottom = p.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.coyote_timer = self.coyote_max
                elif self.vel_y < 0:
                    self.rect.top = p.bottom
                    self.vel_y = 0

        if not self.on_ground and self.coyote_timer > 0:
            self.coyote_timer -= 1


# --- 2. THE ENVIRONMENT CLASS ---
class PlatformerEnv(gym.Env):
    def __init__(self):
        super(PlatformerEnv, self).__init__()
        
        # 0: Idle, 1: Left, 2: Right, 3: Jump, 4: Jump Left, 5: Jump Right
        self.action_space = spaces.Discrete(6)
        
        # Vision: 15x15 grid (Radius of 7 = 15 tiles. 15 * 15 = 225)
        self.observation_space = spaces.Box(low=-1.0, high=3.0, shape=(121,), dtype=np.float32)
        
        self.player = Player(0, 0)
        self.level_data = []
        self.max_steps = 1000 # Give it 700 frames to beat the level

    def reset(self, seed=None):
        super().reset(seed=seed)
        
        # Dummy level for testing
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
            'P                           W                W        P',
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
            'G        W                                  W         P',
            'PPPPP    PP     PP      PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP',
            'P                       P',
            'PKKKKKKKKKKKKKKKKKKKKKKKP',
            'PPPPPPPPPPPPPPPPPPPPPPPPP'
        ]
        
        # Physics hitboxes
        self.platforms = []
        self.hazards = []
        self.finish_blocks = []
        self.waypoints = []
        start_x, start_y = 0, 0
        
        for r, row in enumerate(self.level_data):
            for c, char in enumerate(row):
                x = c * TILE_SIZE
                y = r * TILE_SIZE
                
                if char == 'P': self.platforms.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
                elif char == 'K' or char == 'k': self.hazards.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
                elif char == 'G': self.finish_blocks.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
                elif char == 'S': 
                    start_x, start_y = x, y
                elif char == 'W':
                    self.waypoints.append((c, r)) 
                    
        self.waypoints.sort(key=lambda wp: wp[0])
        
        self.player.reset_position(start_x, start_y)
        self.current_step = 0
        self.current_wp_index = 0
        self.closest_dist = float('inf')
        
        return self._get_observation(), {}

    def step(self, action):
        self.current_step += 1
        reward = 0
        done = False
        truncated = False
        
        # --- 1. AI CONTROLS ---
        move_l = action in [1, 4]
        move_r = action in [2, 5]
        jump = action in [3, 4, 5]
        
        # The Jump Penalty! Stops the AI from pogo-sticking everywhere.
        if jump:
            reward -= 0.05 
            
        # --- 2. RUN REAL PHYSICS ENGINE ---
        self.player.update(self.platforms, [], self.hazards, [], self.finish_blocks, move_l, move_r, jump)

        # --- 3. REWARDS & COLLISIONS ---
        # Did they hit spikes? (Using actual hitbox collision now!)
        for h in self.hazards:
            if self.player.rect.colliderect(h):
                reward -= 5.0
                done = True
                print("AI Died to Spikes!")
                break

        # Did they touch the Goal?
        for g in self.finish_blocks:
            if self.player.rect.colliderect(g):
                reward += 1000.0 
                done = True
                print("AI BEAT THE LEVEL!")
                break

        # --- 4. WAYPOINT BREADCRUMBS ---
        if self.current_wp_index < len(self.waypoints):
            target_x, target_y = self.waypoints[self.current_wp_index]
            
            # Convert player pixel coordinates into Grid coordinates for the math
            grid_x = self.player.rect.centerx / TILE_SIZE
            grid_y = self.player.rect.centery / TILE_SIZE
            
            dist = math.hypot(target_x - grid_x, target_y - grid_y)
            
            # Only reward the AI if it beats its previous best distance!
            if dist < self.closest_dist:
                distance_improvement = self.closest_dist - dist
                # Reward based on how much closer it got
                if self.closest_dist != float('inf'):
                    reward += distance_improvement * 2.0 
                self.closest_dist = dist
            
            # If AI gets within 1.5 grid blocks of the Waypoint
            if dist < 1.5: 
                self.current_wp_index += 1 
                reward += 10.0 # Tasty breadcrumb!
                self.closest_dist = float('inf') # Reset record for the next waypoint
                
        # --- 5. TIMEOUT CLOCK ---
        if self.current_step >= self.max_steps and not done:
            reward -= 5.0 # Punish it for wasting time
            done = True
            truncated = True
            print("AI Ran out of time!")

        return self._get_observation(), reward, done, truncated, {}

    def _get_observation(self):
        """Creates the 15x15 vision cone around the AI."""
        vision_radius = 5
        obs = []
        
        # Translate the center of the player's hitbox into a grid coordinate
        int_x = int(self.player.rect.centerx // TILE_SIZE)
        int_y = int(self.player.rect.centery // TILE_SIZE)
        
        for r in range(int_y - vision_radius, int_y + vision_radius + 1):
            for c in range(int_x - vision_radius, int_x + vision_radius + 1):
                if r < 0 or r >= len(self.level_data) or c < 0 or c >= len(self.level_data[0]):
                    obs.append(1.0) # Wall
                else:
                    tile = self.level_data[r][c]
                    if tile == 'P': obs.append(1.0)
                    elif tile == 'K' or tile == 'k': obs.append(-1.0)
                    elif tile == 'W': obs.append(3.0)
                    elif tile == 'G': obs.append(2.0)
                    else: obs.append(0.0) 
                        
        return np.array(obs, dtype=np.float32)

    def render(self, mode="human"):
        """Draws a simple Pygame window to watch the AI learn."""
        if not hasattr(self, 'screen'):
            pygame.init()
            self.cell_size = 25 
            width = len(self.level_data[0]) * self.cell_size
            height = len(self.level_data) * self.cell_size
            self.screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption("AI Training Vision")
            self.clock = pygame.time.Clock()

        self.screen.fill((0, 0, 0))

        # Draw the map
        for r, row in enumerate(self.level_data):
            for c, char in enumerate(row):
                rect = pygame.Rect(c * self.cell_size, r * self.cell_size, self.cell_size, self.cell_size)
                if char == 'P': pygame.draw.rect(self.screen, (100, 100, 100), rect) 
                elif char == 'K' or char == 'k': pygame.draw.rect(self.screen, (255, 0, 0), rect) 
                elif char == 'G': pygame.draw.rect(self.screen, (0, 255, 0), rect) 
                elif char == 'S': pygame.draw.rect(self.screen, (255, 255, 0), rect, 1) 
                elif char == 'W': pygame.draw.rect(self.screen, (255, 0, 255), rect, 1) # Purple waypoints

        # Draw the AI Player using a converted physical position
        px = (self.player.rect.x / TILE_SIZE) * self.cell_size
        py = (self.player.rect.y / TILE_SIZE) * self.cell_size
        player_rect = pygame.Rect(int(px), int(py), self.cell_size, self.cell_size)
        pygame.draw.rect(self.screen, (0, 150, 255), player_rect) 

        pygame.display.flip()
        self.clock.tick(500) 
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()