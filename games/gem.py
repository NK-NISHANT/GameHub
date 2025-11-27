import pygame, sys, random, requests, math

API_URL = "http://127.0.0.1:5000"
TOKEN, USERNAME = None, "Guest"
if len(sys.argv) > 2:
    TOKEN, USERNAME = sys.argv[1], sys.argv[2]

pygame.init()
WIDTH, HEIGHT = 500, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"Gem Crush Deluxe | {USERNAME}")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 30, bold=True)
score_font = pygame.font.SysFont("Arial", 40, bold=True)
bonus_font = pygame.font.SysFont("Arial", 60, bold=True)

COLORS = [
    (230, 50, 50),   # Red
    (50, 230, 50),   # Green
    (50, 100, 255),  # Blue
    (255, 240, 0),   # Yellow
    (200, 50, 200)   # Purple
]

ROWS, COLS = 8, 8
TILE = 55
OFFSET_X = (WIDTH - (COLS * TILE)) // 2
OFFSET_Y = 180

class FloatingText:
    def __init__(self, text, x, y, color, size_type="normal"):
        self.text = text
        self.x, self.y = x, y
        self.color = color
        self.timer = 120 if size_type == "big" else 60
        self.max_timer = self.timer
        self.size_type = size_type
        self.dy = -0.5 if size_type == "big" else -1.0 

    def update(self):
        self.y += self.dy
        self.timer -= 1

    def draw(self):
        if self.timer > 0:
            alpha = int(255 * (self.timer / self.max_timer))
            f = bonus_font if self.size_type == "big" else score_font
            surf = f.render(str(self.text), True, self.color)
            surf.set_alpha(alpha)
            screen.blit(surf, (self.x - surf.get_width()//2, self.y))

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-4, 4)
        self.color = color
        self.life = random.randint(20, 40)
        self.size = random.randint(3, 6)
        self.gravity = 0.2

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= 1
        self.size = max(0, self.size - 0.1)

    def draw(self):
        if self.life > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))

board, particles, floating_texts, score = [], [], [], 0

def init_board():
    global board
    board = [[random.randint(0,4) for _ in range(COLS)] for _ in range(ROWS)]
    while find_matches():
        board = [[random.randint(0,4) for _ in range(COLS)] for _ in range(ROWS)]

def draw_gem_shape(surface, val, x, y, size):
    rect = pygame.Rect(0, 0, size, size)
    rect.center = (x + size//2, y + size//2)
    col = COLORS[val]
    
    if val == 0: pygame.draw.circle(surface, col, rect.center, size//2)
    elif val == 1: pygame.draw.rect(surface, col, rect, border_radius=5)
    elif val == 2:
        pygame.draw.polygon(surface, col, [(rect.centerx, rect.top), (rect.right, rect.centery), (rect.centerx, rect.bottom), (rect.left, rect.centery)])
    elif val == 3: pygame.draw.ellipse(surface, col, rect)
    elif val == 4:
        pygame.draw.polygon(surface, col, [(rect.centerx, rect.top), (rect.right, rect.bottom), (rect.left, rect.bottom)])

def find_matches():
    matches = set()
    for r in range(ROWS):
        for c in range(COLS-2):
            if board[r][c] == board[r][c+1] == board[r][c+2] != -1:
                matches.update([(r,c), (r,c+1), (r,c+2)])
    for c in range(COLS):
        for r in range(ROWS-2):
            if board[r][c] == board[r+1][c] == board[r+2][c] != -1:
                matches.update([(r,c), (r+1,c), (r+2,c)])
    return list(matches)

def spawn_particles(r, c, val):
    if val == -1: return
    for _ in range(15):
        particles.append(Particle(OFFSET_X + c*TILE + TILE//2, OFFSET_Y + r*TILE + TILE//2, COLORS[val]))

def handle_matches(matches_list):
    global score
    if not matches_list: return False
    
    unique_matches = set(matches_list)
    match_count = len(unique_matches)
    points = match_count * 10
    bonus_text = ""
    
    if match_count >= 6:
        points += 500
        bonus_text = "+500!"
    elif match_count == 5:
        points += 200
        bonus_text = "+200!"
    elif match_count == 4:
        points += 50
        bonus_text = "Bonus!"

    score += points
    
    cr, cc = matches_list[0]
    cx, cy = OFFSET_X + cc*TILE, OFFSET_Y + cr*TILE
    
    if bonus_text:
        col = (255, 215, 0) if match_count >= 5 else (0, 255, 255)
        floating_texts.append(FloatingText(bonus_text, cx, cy, col, "big"))
    else:
        floating_texts.append(FloatingText(f"+{points}", cx, cy, (255, 255, 255)))

    for r, c in unique_matches:
        spawn_particles(r, c, board[r][c])
        board[r][c] = -1
    return True

def apply_gravity():
    for c in range(COLS):
        empty_slots = 0
        for r in range(ROWS-1, -1, -1):
            if board[r][c] == -1:
                empty_slots += 1
            elif empty_slots > 0:
                board[r+empty_slots][c] = board[r][c]
                board[r][c] = -1
    for c in range(COLS):
        for r in range(ROWS):
            if board[r][c] == -1:
                board[r][c] = random.randint(0, 4)

def send_score_api():
    if TOKEN: 
        try: requests.post(f"{API_URL}/api/score", json={"score": score, "game_id": "gem"}, headers={"Authorization": f"Bearer {TOKEN}"})
        except: pass

def main():
    init_board()
    selected = None
    swap_start_time = 0
    swap_pos1, swap_pos2 = None, None
    last_match_time = 0
    state = "IDLE" 
    game_duration = 60000
    start_ticks = pygame.time.get_ticks()

    while True:
        current_time = pygame.time.get_ticks()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                send_score_api()
                pygame.quit(); sys.exit()
            
            if state == "IDLE" and event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                c, r = (mx - OFFSET_X)//TILE, (my - OFFSET_Y)//TILE
                
                if 0<=r<ROWS and 0<=c<COLS:
                    if selected is None:
                        selected = (r, c)
                    else:
                        r1, c1 = selected
                        if abs(r1-r) + abs(c1-c) == 1:
                            swap_pos1, swap_pos2 = (r1,c1), (r,c)
                            board[r1][c1], board[r][c] = board[r][c], board[r1][c1]
                            state = "SWAPPING"
                            swap_start_time = current_time
                        selected = None

        if state == "SWAPPING":
            if current_time - swap_start_time > 200:
                if find_matches(): state = "MATCHING"
                else:
                    r1, c1 = swap_pos1
                    r2, c2 = swap_pos2
                    board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]
                    state = "IDLE"

        elif state == "MATCHING":
            if handle_matches(find_matches()):
                state = "FALLING"
                last_match_time = current_time
            else:
                state = "IDLE"

        elif state == "FALLING":
            if current_time - last_match_time > 300:
                apply_gravity()
                if find_matches(): state = "MATCHING"
                else: state = "IDLE"

        screen.fill((30, 30, 40))
        
        for r in range(ROWS):
            for c in range(COLS):
                val = board[r][c]
                if val == -1: continue
                x, y = OFFSET_X + c*TILE, OFFSET_Y + r*TILE
                draw_gem_shape(screen, val, x+4, y+4, TILE-8)
                if selected == (r, c):
                    pygame.draw.rect(screen, (255,255,255), (x,y,TILE,TILE), 3, border_radius=5)

        for p in particles[:]:
            p.update(); p.draw()
            if p.life <= 0: particles.remove(p)
            
        for ft in floating_texts[:]:
            ft.update(); ft.draw()
            if ft.timer <= 0: floating_texts.remove(ft)

        time_left = max(0, (game_duration - (current_time - start_ticks)) // 1000)
        screen.blit(font.render(f"Score: {score}", True, (255,255,255)), (20, 20))
        screen.blit(font.render(f"Time: {time_left}", True, (255,100,100) if time_left < 10 else (100,255,100)), (WIDTH-140, 20))
        
        if time_left == 0:
            screen.fill((0,0,0))
            txt = bonus_font.render("GAME OVER", True, (255,255,255))
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 50))
            stxt = font.render(f"Final Score: {score}", True, (255,255,0))
            screen.blit(stxt, (WIDTH//2 - stxt.get_width()//2, HEIGHT//2 + 20))
            pygame.display.flip()
            send_score_api()
            time.sleep(3)
            break

        pygame.display.flip()

if __name__ == "__main__":
    main()