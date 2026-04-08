import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
import math
from torch.utils.tensorboard import SummaryWriter

# --- MATCHING PHYSICS CONSTANTS FROM MAIN.PY ---
TILE_SIZE = 30
GRAVITY = 0.8
JUMP_STRENGTH = -17

# --- 1. THE PLAYER CLASS ---
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
        
        # Vision: 11x11 grid (121)
        self.observation_space = spaces.Box(low=-1.0, high=3.0, shape=(361,), dtype=np.float32)
        
        self.player = Player(0, 0)
        self.level_data = []
        self.max_steps = 2000 # Give it 2000 frames to beat the level

    def reset(self, seed=None):
        super().reset(seed=seed)
        
        # Dummy level for testing
        self.level_data = [
            'PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP',
            'P                                                     P',
            'P                                                     P',
            'P                                                     P',
            'P                                                     P',
            'P                                                     P',
            'P                                                     P',
            'P                                                     P',
            'P                                                     P',
            'P                           2        33      44       P',
            'P                           P        PP      PP       P',
            'P                           P                         P',
            'P                           P                         P',
            'P  S         0000    11     P                         P',
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
            'G6        7               6                5          P',
            'PPPPP    PP     PP      PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP',
            'P                       P',
            'PKKKKKKKKKKKKKKKKKKKKKKKP',
            'PPPPPPPPPPPPPPPPPPPPPPPPP'
        ]
        
        # Physics hitboxes
        self.platforms = []
        self.hazards = []
        self.finish_blocks = []
        temp_waypoints = {} 
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
                elif char.isdigit(): 
                    temp_waypoints[int(char)] = (c, r) 
                    
        self.waypoints = [temp_waypoints[i] for i in sorted(temp_waypoints.keys())]
        
        self.player.reset_position(start_x, start_y)
        self.current_step = 0
        self.current_wp_index = 0
        self.closest_dist = float('inf')
        
        return self._get_observation(), {}

    def step(self, action):
        self.current_step += 1
        reward = 0.0
        done = False
        truncated = False
        
        # --- 1. AI CONTROLS ---
        move_l = action in [1, 4]
        move_r = action in [2, 5]
        jump = action in [3, 4, 5]
        
        if jump:
            reward -= 0.5
            
        # --- 2. RUN REAL PHYSICS ENGINE ---
        self.player.update(self.platforms, [], self.hazards, [], self.finish_blocks, move_l, move_r, jump)

        # --- 3. REWARDS & COLLISIONS ---
        for h in self.hazards:
            if self.player.rect.colliderect(h):
                reward -= 5.0
                done = True
                print("AI Died to Spikes!")
                break

        for g in self.finish_blocks:
            if self.player.rect.colliderect(g):
                reward += 1000.0 
                done = True
                print("AI BEAT THE LEVEL!")
                break

        # --- 4. CHECKPOINT BREADCRUMBS ---
        if self.current_wp_index < len(self.waypoints):
            target_x, target_y = self.waypoints[self.current_wp_index]
            
            grid_x = self.player.rect.centerx / TILE_SIZE
            grid_y = self.player.rect.centery / TILE_SIZE
            
            dist = math.hypot(target_x - grid_x, target_y - grid_y)
            
            if dist < self.closest_dist:
                distance_improvement = self.closest_dist - dist
                if self.closest_dist != float('inf'):
                    reward += distance_improvement * 2.0 
                self.closest_dist = dist
            
            if dist < 1.5: 
                self.current_wp_index += 1 
                reward += 10.0 
                self.closest_dist = float('inf') 
                
        # --- 5. TIMEOUT CLOCK ---
        if self.current_step >= self.max_steps and not done:
            reward -= 5.0 
            done = True
            truncated = True
            print("AI Ran out of time!")

        # --- 6. CALCULATE TRUE LEVEL PROGRESS ---
        total_waypoints = len(self.waypoints)
        if total_waypoints > 0:
            progress_percent = (self.current_wp_index / total_waypoints) * 100
        else:
            progress_percent = 0.0

        # Pass checkpoint data safely out of the environment
        info = {
            "level_progress": progress_percent,
            "checkpoint_reached": self.current_wp_index
        }

        return self._get_observation(), reward, done, truncated, info

    def _get_observation(self):
        vision_radius = 9
        obs = []
        
        int_x = int(self.player.rect.centerx // TILE_SIZE)
        int_y = int(self.player.rect.centery // TILE_SIZE)
        
        for r in range(int_y - vision_radius, int_y + vision_radius + 1):
            for c in range(int_x - vision_radius, int_x + vision_radius + 1):
                if r < 0 or r >= len(self.level_data) or c < 0 or c >= len(self.level_data[r]):
                    obs.append(1.0) 
                else:
                    tile = self.level_data[r][c]
                    if tile == 'P': obs.append(1.0)
                    elif tile == 'K' or tile == 'k': obs.append(-1.0)
                    elif tile.isdigit(): obs.append(3.0)
                    elif tile == 'G': obs.append(2.0)
                    else: obs.append(0.0) 
                        
        return np.array(obs, dtype=np.float32)
    
    def render(self, mode="human"):
        if not hasattr(self, 'screen'):
            pygame.init()
            self.cell_size = 25 
            width = len(self.level_data[0]) * self.cell_size
            height = len(self.level_data) * self.cell_size
            self.screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption("AI Training Vision")
            self.clock = pygame.time.Clock()

        self.screen.fill((0, 0, 0))

        for r, row in enumerate(self.level_data):
            for c, char in enumerate(row):
                rect = pygame.Rect(c * self.cell_size, r * self.cell_size, self.cell_size, self.cell_size)
                if char == 'P': pygame.draw.rect(self.screen, (100, 100, 100), rect) 
                elif char == 'K' or char == 'k': pygame.draw.rect(self.screen, (255, 0, 0), rect) 
                elif char == 'G': pygame.draw.rect(self.screen, (0, 255, 0), rect) 
                elif char == 'S': pygame.draw.rect(self.screen, (255, 255, 0), rect, 1) 
                elif char.isdigit(): pygame.draw.rect(self.screen, (255, 0, 255), rect, 1)
                
        px = (self.player.rect.x / TILE_SIZE) * self.cell_size
        py = (self.player.rect.y / TILE_SIZE) * self.cell_size
        player_rect = pygame.Rect(int(px), int(py), self.cell_size, self.cell_size)
        pygame.draw.rect(self.screen, (0, 150, 255), player_rect) 

        pygame.display.flip()
        self.clock.tick(60) 
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()


# =====================================================================
# --- 3. TRAINING LOOP & TENSORBOARD INTEGRATION ---
# =====================================================================
# This is the section that actually RUNS the classes defined above!
if __name__ == "__main__":
    
    env = PlatformerEnv()
    writer = SummaryWriter('runs/platformer_ai_training')
    
    num_episodes = 1000
    log_interval = 10 
    
    progress_this_batch = []
    checkpoints_this_batch = [] 
    
    print("Starting AI Training Loop...")
    
    for episode in range(num_episodes):
        obs, _ = env.reset()
        done = False
        truncated = False
        
        final_progress = 0
        final_checkpoint = 0
        
        while not (done or truncated):
            action = env.action_space.sample() # The AI mashing random buttons for testing

            
            obs, reward, done, truncated, info = env.step(action)
            
            # env.render() # Uncomment this if you want to watch the Pygame window!
            
            final_progress = info.get("level_progress", 0)
            final_checkpoint = info.get("checkpoint_reached", 0) 
            
        progress_this_batch.append(final_progress)
        checkpoints_this_batch.append(final_checkpoint)
        
        if (episode + 1) % log_interval == 0:
            
            avg_progress = np.mean(progress_this_batch)
            avg_checkpoint = np.mean(checkpoints_this_batch)
            
            writer.add_scalar('Progress/Average_Level_Percent', avg_progress, episode)
            writer.add_scalar('Progress/Average_Waypoint_reached', avg_checkpoint, episode)
            writer.flush()
            
            progress_this_batch = []
            checkpoints_this_batch = []

    print("Training Finished!")
    writer.close()
    pygame.quit()