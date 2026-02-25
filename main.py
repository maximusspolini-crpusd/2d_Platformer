import pygame


# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 20
GRAVITY = 0.8
JUMP_STRENGTH = -17
PLAYER_SPEED = 5

# Colors
BG_COLOR = (30, 30, 40)
PLAYER_COLOR = (50, 200, 150)
PLATFORM_COLOR = (100, 100, 120)
HAZARD_COLOR = (255, 0, 0)

show_controls = True

START_X = 49
START_Y = 270

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Platformer - Camera System")
clock = pygame.time.Clock()

# --- LEVEL DESIGN ---
LEVEL_MAP = [
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP",
    "Pkkk                                                  P",
    "Pkkk                                                  P",
    "P                                                     P",
    "P                                                     P",
    "P                                                     P",
    "P                                                     P",
    "P                                                     P",
    "P                                                     P",
    "P                                                     P",
    "P                           P        PP      PP       P",
    "P                           P                         P",
    "P                           P                         P",
    "P                           PKKKKKKKKKKKKKKKKKK       P",
    "PPPPP          PP           PPPPPPPPPPPPPPPPPPP       P",
    "KKKKKKKKKKKKKKKKKKKKKKKKKKKKPPPPPPPPPPPPPPPPPPP       P",
    "P                                                     P",
    "P                                                     P",
    "P                                                     P",
    "P                                                     P",
    "P                                                     P",
    "P                                                     P",
    "P                                                     P",
    "P                                                     P",
    "P                                                     P",
    "P                                                     P",
    "PPP      P     PP       PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP",
    "P                       P               ",
    "PKKKKKKKKKKKKKKKKKKKKKKKP               ",
    "PPPPPPPPPPPPPPPPPPPPPPPPP                        "
]

# Parse the level map
platforms = []
hazards = []
ihazards = []

for row_index, row in enumerate(LEVEL_MAP):
    for col_index, cell in enumerate(row):
        if cell == "P":
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE
            platforms.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
        if cell == "K":
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE
            hazards.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
        if cell == "k":
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE
            ihazards.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))    

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
        

    def update(self, platforms, hazards, ihazards):
        dx = 0
        dy = 0

        # Horizontal Movement
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

        # Apply Gravity
        self.vel_y += GRAVITY
        dy = self.vel_y

        # Vertical Movement
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

# Create player
player = Player(50, 50)
running = True

# Camera variables
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
                player.reset_position()
            if event.key == pygame.K_TAB:
                show_controls = True
            elif event.key == pygame.K_c:
                print(f"Player Position -> X: {player.rect.x}, Y: {player.rect.y}")

        if event.type == pygame.VIDEORESIZE:
            SCREEN_WIDTH, SCREEN_HEIGHT = event.size
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
       
    player.update(platforms, hazards, ihazards)
         
    for hazard in hazards:
        if player.rect.colliderect(hazard):
            player.reset_position()

    for ihazard in ihazards:
        if player.rect.colliderect(ihazard):
            player.reset_position()
    
    
    # --- CAMERA LOGIC ---
    # Calculate the camera offset so the player is always in the center of the screen
    camera_x = player.rect.x - (SCREEN_WIDTH // 2)
    camera_y = player.rect.y - (SCREEN_HEIGHT // 2)
    
    # Draw Everything
    screen.fill(BG_COLOR)
    
    # Draw platforms with the camera offset applied
    for platform in platforms:
        # .move() creates a temporary rectangle shifted by the camera amount
        shifted_platform = platform.move(-camera_x, -camera_y)
        pygame.draw.rect(screen, PLATFORM_COLOR, shifted_platform)
        
    for hazard in hazards:
        shifted_hazard = hazard.move(-camera_x, -camera_y)
        pygame.draw.rect(screen, HAZARD_COLOR, shifted_hazard)
        
        
    # Draw player with the camera offset applied
    shifted_player = player.rect.move(-camera_x, -camera_y)
    pygame.draw.rect(screen, PLAYER_COLOR, shifted_player)
    
    if show_controls:
        # Create a semi-transparent dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180) # 0 is invisible, 255 is solid
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0,0))

        # Setup Font
        instr_font = pygame.font.SysFont("Arial", 30, bold=True)
        
        # Render instructions
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
            # Center the text
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, 150 + (i * 40)))
            screen.blit(text_surf, text_rect)
            
        

    pygame.display.flip()
    clock.tick(60)


        


pygame.quit()