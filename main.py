import pygame


# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 30
GRAVITY = 0.8
JUMP_STRENGTH = -17
PLAYER_SPEED = 5

# Colors
BG_COLOR = (0, 0, 0)
PLAYER_COLOR = (50, 200, 150)
PLATFORM_COLOR = (100, 100, 120)
HAZARD_COLOR = (255, 0, 0)
GOAL_COLOR = (0, 255, 0)

# Cooldown settings
teleport_cooldown = 100  # 100 milliseconds = .1 seconds
last_teleport_time = 0   

show_controls = True

START_X = 55
START_Y = 280

current_level = 1  
ui_font = pygame.font.SysFont("Arial", 28, bold=True)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Platformer - Camera System")
clock = pygame.time.Clock()

def load_level(level_number):
    global platforms, hazards, finish_blocks, START_X, START_Y, ihazards
    

    platforms = []
    hazards = []
    ihazards = []
    finish_blocks = []


    file_path = f"levels/{level_number}.txt"
    try:
        with open(file_path, 'r') as f:
            level_data = [line.strip('\n') for line in f.readlines()]
            

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
                    
        # 4. Put the player at the new start
        player.reset_position()
        
    except FileNotFoundError:
        print(f"Error: {file_path} not found! Returning to Level 1.")
        
        load_level(1) 
        
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
        self.coyote_max = 8  
    
    def reset_position(self):
        self.vel_y = 0
        self.vel_x = 0
        self.rect.x = START_X
        self.rect.y = START_Y
        
        

    def update(self, platforms, hazards, ihazards, goal):


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

        if not self.on_ground and self.coyote_timer > 0:
            self.coyote_timer -= 1

    def draw(self, surface):
        pygame.draw.rect(surface, PLAYER_COLOR, self.rect)


player = Player(50, 50)
load_level(current_level)
running = True


camera_x = 0
camera_y = 0

# --- MAIN GAME LOOP ---
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN:
            show_controls = False
            if event.key == pygame.K_r:
                load_level(current_level)
            if event.key == pygame.K_TAB:
                show_controls = True
            if event.key == pygame.K_g:
                current_level += 1
                load_level(current_level)
                if current_level > 4:
                    current_level = 1
            elif event.key == pygame.K_c:
                print(f"Player Position -> X: {player.rect.x}, Y: {player.rect.y}")

        if event.type == pygame.VIDEORESIZE:
            SCREEN_WIDTH, SCREEN_HEIGHT = event.size
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
       
    player.update(platforms, hazards, ihazards, finish_blocks)
         
    for hazard in hazards:
        if player.rect.colliderect(hazard):
            player.reset_position()

    for ihazard in hazards:
        if player.rect.colliderect(ihazard):
            player.reset_position()

    for finish in finish_blocks:
        if player.rect.colliderect(finish):
            current_level += 1
            load_level(current_level)
            if current_level > 4:
                current_level = 1

            
            
            
            
        
        
        
        
        
        
        
        
        
        

# Inside your 'while running' event loop:
    if event.type == pygame.MOUSEBUTTONDOWN:
        current_time = pygame.time.get_ticks()
        
        # Check if the cooldown has passed
        if current_time - last_teleport_time >= teleport_cooldown:
            mx, my = pygame.mouse.get_pos()
            
            # Teleport player (accounting for camera offset)
            player.rect.x = mx + camera_x
            player.rect.y = my + camera_y
            player.vel_y = 0
            
            # Update the timestamp
            last_teleport_time = current_time

        else:
            seconds_left = (teleport_cooldown - (current_time - last_teleport_time)) / 1000
        
        
        
        
        
        
        
        
        
        
                
    
    
    
    # --- CAMERA LOGIC ---
    camera_x = player.rect.x - (SCREEN_WIDTH // 2)
    camera_y = player.rect.y - (SCREEN_HEIGHT // 2)
    screen.fill(BG_COLOR)
    





    

    
   
    for platform in platforms:
        
        shifted_platform = platform.move(-camera_x, -camera_y)
        pygame.draw.rect(screen, PLATFORM_COLOR, shifted_platform)
        
    for hazard in hazards:
        shifted_hazard = hazard.move(-camera_x, -camera_y)
        pygame.draw.rect(screen, HAZARD_COLOR, shifted_hazard)
        
    for finish in finish_blocks:
        shifted_finish = finish.move(-camera_x, -camera_y)
        pygame.draw.rect(screen, GOAL_COLOR, shifted_finish)
        
        

    shifted_player = player.rect.move(-camera_x, -camera_y)
    pygame.draw.rect(screen, PLAYER_COLOR, shifted_player)
    
   
    
    if show_controls:
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
            "R - Reset Position",
            "C - Print Coordinates",
            "",
            "Press any key to START"
        ]

        for i, line in enumerate(lines):
            text_surf = instr_font.render(line, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, 150 + (i * 40)))
            screen.blit(text_surf, text_rect)
            
        

    # --- DRAW UI ---
    level_text = ui_font.render(f"LEVEL: {current_level}", True, (255, 255, 255))
    level_rect = level_text.get_rect(topright=(SCREEN_WIDTH - 20, 20))
    bg_rect = level_rect.inflate(20, 10) 
    pygame.draw.rect(screen, (0, 0, 0, 0), bg_rect, border_radius=5)
    screen.blit(level_text, level_rect)

    pygame.display.flip()
    clock.tick(60)


        


pygame.quit()