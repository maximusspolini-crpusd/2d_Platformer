import pygame



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
debug = False

teleport_cooldown = 100  # 100 milliseconds = .1 seconds
last_teleport_time = 0   
controls_showing = True
zoom = 1.0  


def get_screen_coords(x, y, camera_x, camera_y, zoom):
    screen_x = (x - camera_x) * zoom + (SCREEN_WIDTH / 2)
    screen_y = (y - camera_y) * zoom + (SCREEN_HEIGHT / 2)
    return screen_x, screen_y


def get_world_coords(mouse_x, mouse_y, camera_x, camera_y, zoom):
    world_x = (mouse_x - (SCREEN_WIDTH / 2)) / zoom + camera_x
    world_y = (mouse_y - (SCREEN_HEIGHT / 2)) / zoom + camera_y
    return world_x, world_y




START_X = 0
START_Y = 0

current_level = 1  
ui_font = pygame.font.SysFont("Arial", 28, bold=True)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Platformer - Camera System")
clock = pygame.time.Clock()

# --------------------------------------
# made by me
# --------------------------------------

def load_level(level_number):
    global platforms, hazards, finish_blocks, START_X, START_Y, ihazards, checkpoints, long_platforms, adjusted_x
    
    #lists used to store the level data

    platforms = []
    long_platforms = []
    hazards = []
    ihazards = []
    finish_blocks = []
    checkpoints = []



    # use level_number to select the correct file to parse
    file_path = f"levels/{level_number}.txt"
    try:
        with open(file_path, 'r') as f:
            level_data = [line.strip('\n') for line in f.readlines()]
            
        # goes through each line and row and adds the level data in the correct list above
        
        for row_index, row in enumerate(level_data):
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
                    
                    
        #set player to start location
        player.reset_position()
    # catch the error so python doesnt through a fit when it catches an error
    except FileNotFoundError:
        print(f"Error: {file_path} not found! Returning to Level 1.")
        
        load_level(1) 
        

def show_controls(controls_showing):
    if controls_showing:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0,0))

        instr_font = pygame.font.SysFont("Arial", 30, bold=True)
        

        lines = [
            "CONTROLS",
            "Tab - Show this agan",
            "A / D - Move Left & Right",
            "SPACE - Jump",
            "R - Restart Level",
            "",
            "Press any key to EXIT"
        ]

        for i, line in enumerate(lines):
            text_surf = instr_font.render(line, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, 150 + (i * 40)))
            screen.blit(text_surf, text_rect)

# -------------------
# made by ai
# -------------------
        
# --- PLAYER CLASS ---
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.vel_y = 0
        self.vel_x = 0
        self.on_ground = False
        
        self.accel = 0.8
        self.air_friction = 0.8
        self.ground_friction = 0.7
        self.max_speed = 5
        
        self.coyote_timer = 0
        self.coyote_max = 60
        
    # -------------------------
    #   Made by me
    # -------------------------
    def reset_position(self):
        self.vel_y = 0
        self.vel_x = 0
        self.rect.x = START_X
        self.rect.y = START_Y
        
        
        
    # -------------------------
    #   Made by AI
    # ------------------------
    
    def update(self, platforms, long_platforms, hazards, ihazards, goal):


        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.vel_x -= self.max_speed
        if keys[pygame.K_d]:
            self.vel_x += self.max_speed
        else:
            if self.on_ground:  
                self.vel_x *= self.ground_friction
            else:
                self.vel_x *= self.air_friction
            
        if self.vel_x > self.max_speed: self.vel_x = self.max_speed
        if self.vel_x < -self.max_speed: self.vel_x = -self.max_speed
        
        if abs(self.vel_x) < 0.1:
            self.vel_x = 0
            
        #terminal velo
        if self.vel_y > 15:
            self.vel_y = 15

        dy = self.vel_y

        
        
        self.rect.x += self.vel_x
            
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel_x > 0: 
                    self.rect.right = platform.left
                    self.vel_x = 0
                elif self.vel_x < 0: 
                    self.rect.left = platform.right
                    self.vel_x = 0
                    
        for lplatform in long_platforms:
            if self.rect.colliderect(lplatform):
                if self.vel_x > 0:
                    self.rect.right = lplatform.left
                    self.vel_x = 0
                elif self.vel_x < 0:
                    self.rect.left = lplatform.right
                    self.vel_x = 0
            

        # --- JUMP LOGIC  ---
        if keys[pygame.K_SPACE] and self.coyote_timer > 0:
            self.vel_y = JUMP_STRENGTH
            self.coyote_timer = 0  
            self.on_ground = False


        self.vel_y += GRAVITY
        dy = self.vel_y


        self.rect.y += dy
        self.on_ground = False 
        
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel_y > 0: 
                    self.rect.bottom = platform.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.coyote_timer = self.coyote_max 
                elif self.vel_y < 0: 
                    self.rect.top = platform.bottom
                    self.vel_y = 0

        for lplatform in long_platforms:
            if self.rect.colliderect(lplatform):
                if self.vel_y > 0: 
                    self.rect.bottom = lplatform.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.coyote_timer = self.coyote_max 
                elif self.vel_y < 0: 
                    self.rect.top = lplatform.bottom
                    self.vel_y = 0


        if not self.on_ground and self.coyote_timer > 0:
            self.coyote_timer -= 1

    def draw(self, surface):
        pygame.draw.rect(surface, PLAYER_COLOR, self.rect)


player = Player(50, 50)
load_level(current_level)
running = True






camera_x = player.rect.centerx
camera_y = player.rect.centery

# --- MAIN GAME LOOP ---
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # ----------------------------
        #   Made by me
        # ----------------------------
        
        
        # SKIP LEVEL IS A DEBUG FEATURE
        if event.type == pygame.KEYDOWN:
            controls_showing = False
            if event.key == pygame.K_r:
                load_level(current_level)
            if event.key == pygame.K_g:
                if debug == True:
                    current_level = (current_level + 1)
                
                if current_level > 6:
                    current_level = 1
                load_level(current_level)
            if event.key == pygame.K_TAB:
                controls_showing = True

        # ----------------------------
        #   Made by AI 
        # ----------------------------
        if event.type == pygame.VIDEORESIZE:
            SCREEN_WIDTH, SCREEN_HEIGHT = event.size
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)

        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0: zoom = min(2.0, zoom + 0.1)
            elif event.y < 0: zoom = max(0.2, zoom - 0.1)

        # --------------------------------
        # TELEPORT IS A DEBUG FEATURE
        # --------------------------------

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                if debug == True:
                    current_time = pygame.time.get_ticks()
                    if current_time - last_teleport_time >= teleport_cooldown:
                        mx, my = pygame.mouse.get_pos()
                        # Use inverse math to find where we clicked in the real world
                        tx, ty = get_world_coords(mx, my, camera_x, camera_y, zoom)
                        player.rect.center = (tx, ty) # Teleport center to mouse
                        player.vel_y = 0
                        last_teleport_time = current_time


    player.update(platforms, long_platforms, hazards, ihazards, finish_blocks)
    

    camera_x = player.rect.centerx
    camera_y = player.rect.centery

    # --------------------------
    # made by me
    # --------------------------

    for h in hazards + ihazards:
        if player.rect.colliderect(h):
            player.reset_position()
    for finish in finish_blocks:
        if player.rect.colliderect(finish):
            current_level = (current_level % 6) + 1
            load_level(current_level)
    for c in checkpoints:
        if player.rect.colliderect(c):
            START_X, START_Y = c.centerx - (player.rect.width / 2), c.top - player.rect.height
            checkpoint_color = (255, 255, 10)

    # ------------------------
    # made by ai
    # ------------------------
    
    screen.fill(BG_COLOR)
    current_tile_size = TILE_SIZE * zoom
    current_checkpoint_size_x = CHECKPOINT_SIZE_x * zoom
    current_checkpoint_size_y = CHECKPOINT_SIZE_y * zoom
    current_long_platforms_x = long_platforms_x * zoom

    # draw hazards
    for h in hazards:
        sx, sy = get_screen_coords(h.x, h.y, camera_x, camera_y, zoom)
        pygame.draw.rect(screen, HAZARD_COLOR, (sx, sy, current_tile_size, current_tile_size))
        
    # draw goals
    for g in finish_blocks:
        sx, sy = get_screen_coords(g.x, g.y, camera_x, camera_y, zoom)
        pygame.draw.rect(screen, GOAL_COLOR, (sx, sy, current_tile_size, current_tile_size))

    # draw platforms
    for p in platforms:
        sx, sy = get_screen_coords(p.x, p.y, camera_x, camera_y, zoom)
        pygame.draw.rect(screen, PLATFORM_COLOR, (sx, sy, current_tile_size, current_tile_size))

    for lp in long_platforms:
        sx, sy = get_screen_coords(lp.x, lp.y, camera_x, camera_y, zoom)
        pygame.draw.rect(screen, PLATFORM_COLOR, (sx, sy, current_long_platforms_x, current_tile_size))
    
    for c in checkpoints:
        sx, sy = get_screen_coords(c.x, c.y, camera_x, camera_y, zoom)
        is_claimed = (START_X == c.centerx - (player.rect.width / 2) and START_Y == c.top - player.rect.height)
        current_color = (255, 255, 10) if is_claimed else (255, 255, 255)
        pygame.draw.rect(screen, current_color, (sx, sy, current_checkpoint_size_x, current_checkpoint_size_y))

    # Draw Player (Centered by the math in get_screen_coords)
    px, py = get_screen_coords(player.rect.x, player.rect.y, camera_x, camera_y, zoom)
    scaled_p_width = player.rect.width * zoom
    scaled_p_height = player.rect.height * zoom
    pygame.draw.rect(screen, PLAYER_COLOR, (px, py, scaled_p_width, scaled_p_height))


    
    level_text = ui_font.render(f"LEVEL: {current_level}", True, (255, 255, 255))
    text_rect = level_text.get_rect(topright=(SCREEN_WIDTH - 20, 20))
    
    if controls_showing:
        show_controls(True)
    
    ui_bg = pygame.Surface(text_rect.inflate(20, 10).size, pygame.SRCALPHA)
    ui_bg.fill((255, 255, 255, 50)) 
    screen.blit(ui_bg, text_rect.move(-10, -5))
    screen.blit(level_text, text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()