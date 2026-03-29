import pygame
from stable_baselines3 import PPO
import numpy as np
import os


pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 30
CHECKPOINT_SIZE_x = 30
CHECKPOINT_SIZE_y = 90
GRAVITY = 0.8
JUMP_STRENGTH = -17
PLAYER_SPEED = 5
long_platforms_x = 34.5

# Colors
BG_COLOR = (0, 0, 0)
PLAYER_COLOR = (50, 200, 150)
PLATFORM_COLOR = (100, 100, 120)
HAZARD_COLOR = (255, 0, 0)
GOAL_COLOR = (0, 255, 0)
checkpoint_color = (255, 255, 255)

# Game State
debug = False
ai_is_playing = True # SET THIS TO FALSE IF YOU WANT TO PLAY MANUALLY
current_level = 1  
zoom = 1.0  
teleport_cooldown = 100
last_teleport_time = 0   
controls_showing = True
current_level_map = [] # To store text data for AI vision

# UI
ui_font = pygame.font.SysFont("Arial", 28, bold=True)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Platformer - AI vs Player")
clock = pygame.time.Clock()

# --- UTILITY FUNCTIONS ---
def get_screen_coords(x, y, camera_x, camera_y, zoom):
    screen_x = (x - camera_x) * zoom + (SCREEN_WIDTH / 2)
    screen_y = (y - camera_y) * zoom + (SCREEN_HEIGHT / 2)
    return screen_x, screen_y

def get_world_coords(mouse_x, mouse_y, camera_x, camera_y, zoom):
    world_x = (mouse_x - (SCREEN_WIDTH / 2)) / zoom + camera_x
    world_y = (mouse_y - (SCREEN_HEIGHT / 2)) / zoom + camera_y
    return world_x, world_y

def get_ai_observation(level_data, player_grid_x, player_grid_y):
    """Crops a 11x11 grid around the player for the AI brain."""
    vision_radius = 5
    obs = []
    int_y = int(player_grid_y)
    int_x = int(player_grid_x)
    
    for r in range(int_y - vision_radius, int_y + vision_radius + 1):
        for c in range(int_x - vision_radius, int_x + vision_radius + 1):
            if r < 0 or r >= len(level_data) or c < 0 or c >= len(level_data[0]):
                obs.append(1.0) # Treat out of bounds as Wall
            else:
                tile = level_data[r][c]
                if tile == 'P' or tile == 'L': obs.append(1.0) # Platforms
                elif tile == 'K' or tile == 'k': obs.append(-1.0) # Hazards
                elif tile == 'G': obs.append(2.0) # Goal
                else: obs.append(0.0) # Empty space
    return np.array(obs, dtype=np.float32)

def load_level(level_number):
    global platforms, hazards, finish_blocks, START_X, START_Y, ihazards, checkpoints, long_platforms, current_level_map
    platforms, long_platforms, hazards, ihazards, finish_blocks, checkpoints = [], [], [], [], [], []

    file_path = f"levels/{level_number}.txt"
    try:
        with open(file_path, 'r') as f:
            current_level_map = [line.strip('\n') for line in f.readlines()]
            
        for row_index, row in enumerate(current_level_map):
            for col_index, cell in enumerate(row):
                x, y = col_index * TILE_SIZE, row_index * TILE_SIZE
                if cell == "P":
                    platforms.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
                elif cell == "K":
                    hazards.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
                elif cell == "k":
                    ihazards.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
                elif cell == "G":
                    finish_blocks.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
                elif cell == "S": 
                    START_X, START_Y = x, y
                elif cell == "C":
                    checkpoints.append(pygame.Rect(x, y, CHECKPOINT_SIZE_x, CHECKPOINT_SIZE_y))
                elif cell == "L":
                    adjusted_x = x - (long_platforms_x - TILE_SIZE)
                    long_platforms.append(pygame.Rect(adjusted_x, y, long_platforms_x, TILE_SIZE))
        player.reset_position()
    except FileNotFoundError:
        print(f"Error: {file_path} not found!")

def show_controls():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0,0))
    instr_font = pygame.font.SysFont("Arial", 30, bold=True)
    lines = ["CONTROLS", "Tab - Show this", "A / D - Move", "SPACE - Jump", "R - Restart", "M - Toggle AI Mode", "", "Press any key to EXIT"]
    for i, line in enumerate(lines):
        text_surf = instr_font.render(line, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, 150 + (i * 40)))
        screen.blit(text_surf, text_rect)

# --- PLAYER CLASS ---
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
        self.coyote_max = 10 # Adjusted for better control

    def reset_position(self):
        self.vel_x = 0
        self.vel_y = 0
        self.rect.x = START_X
        self.rect.y = START_Y

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

# Initializing Objects
player = Player(0, 0)
load_level(current_level)

# Load AI
print("Loading AI Brain...")
try:
    ai_brain = PPO.load("smart_platformer_bot")
    print("AI Brain Loaded Successfully!")
except:
    print("Warning: smart_platformer_bot.zip not found. Manual play only.")
    ai_is_playing = False

# Main Loop
running = True
camera_x, camera_y = player.rect.center

while running:
    # 1. Inputs/Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            controls_showing = False
            if event.key == pygame.K_r: load_level(current_level)
            if event.key == pygame.K_TAB: controls_showing = True
            if event.key == pygame.K_m: ai_is_playing = not ai_is_playing
        if event.type == pygame.VIDEORESIZE:
            SCREEN_WIDTH, SCREEN_HEIGHT = event.size
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        if event.type == pygame.MOUSEWHEEL:
            zoom = max(0.2, min(2.0, zoom + (event.y * 0.1)))

    # 2. AI Decision vs Player Input
    # --- AI DECISION MAKING ---
    if ai_is_playing:
        # Use round() instead of // so the AI "sees" the next tile 
        # as soon as it's more than halfway across the current one.
        grid_x = round(player.rect.x / TILE_SIZE)
        grid_y = round(player.rect.y / TILE_SIZE)
        
        # Get vision based on the rounded grid position
        obs = get_ai_observation(current_level_map, grid_x, grid_y)
        # Add a print here to debug if it's still stuck!
        # print(f"AI Position: {grid_x}, {grid_y} | Vision: {obs[:5]}") 
        
        action, _ = ai_brain.predict(obs, deterministic=False)
        
        move_l = action in [1, 4]
        move_r = action in [2, 5]
        jump = action in [3, 4, 5]
    else:
        keys = pygame.key.get_pressed()
        move_l = keys[pygame.K_a]
        move_r = keys[pygame.K_d]
        jump = keys[pygame.K_SPACE]

    # 3. Physics & Camera
    player.update(platforms, long_platforms, hazards, ihazards, finish_blocks, move_l, move_r, jump)
    camera_x += (player.rect.centerx - camera_x) * 0.1
    camera_y += (player.rect.centery - camera_y) * 0.1

    # 4. Logic (Hazards/Goals)
    for h in hazards + ihazards:
        if player.rect.colliderect(h): player.reset_position()
    for f in finish_blocks:
        if player.rect.colliderect(f):
            current_level = (current_level % 6) + 1
            load_level(current_level)

    # 5. Drawing
    screen.fill(BG_COLOR)
    c_tile = TILE_SIZE * zoom
    
    # Draw World Elements
    for h in hazards:
        sx, sy = get_screen_coords(h.x, h.y, camera_x, camera_y, zoom)
        pygame.draw.rect(screen, HAZARD_COLOR, (sx, sy, c_tile, c_tile))
    for g in finish_blocks:
        sx, sy = get_screen_coords(g.x, g.y, camera_x, camera_y, zoom)
        pygame.draw.rect(screen, GOAL_COLOR, (sx, sy, c_tile, c_tile))
    for p in platforms:
        sx, sy = get_screen_coords(p.x, p.y, camera_x, camera_y, zoom)
        pygame.draw.rect(screen, PLATFORM_COLOR, (sx, sy, c_tile, c_tile))
    for lp in long_platforms:
        sx, sy = get_screen_coords(lp.x, lp.y, camera_x, camera_y, zoom)
        pygame.draw.rect(screen, PLATFORM_COLOR, (sx, sy, long_platforms_x * zoom, c_tile))

    # Draw Player
    px, py = get_screen_coords(player.rect.x, player.rect.y, camera_x, camera_y, zoom)
    pygame.draw.rect(screen, PLAYER_COLOR, (px, py, player.rect.width * zoom, player.rect.height * zoom))

    # UI
    mode_text = "AI MODE" if ai_is_playing else "MANUAL MODE"
    lvl_surf = ui_font.render(f"LEVEL: {current_level} | {mode_text}", True, (255, 255, 255))
    screen.blit(lvl_surf, (20, 20))

    if controls_showing: show_controls()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()