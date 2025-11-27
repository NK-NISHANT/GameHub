import pygame, sys, random, requests

API_URL = "http://127.0.0.1:5000"
TOKEN, USERNAME = None, "Guest"
if len(sys.argv) > 2: TOKEN, USERNAME = sys.argv[1], sys.argv[2]

pygame.init()
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"Memory Pro | {USERNAME}")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 30, bold=True)
large_font = pygame.font.SysFont("Arial", 50, bold=True)

TILE_SIZE, GAP = 100, 20
MARGIN_X, MARGIN_Y = 70, 120

particles = []

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y, self.color = x, y, color
        self.vx, self.vy = random.uniform(-5, 5), random.uniform(-5, 5)
        self.life = 40
    def update(self):
        self.x += self.vx; self.y += self.vy; self.life -= 1
    def draw(self):
        if self.life > 0: pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 4)

class Card:
    def __init__(self, val, r, c):
        self.val = val
        self.rect = pygame.Rect(MARGIN_X + c*(120), MARGIN_Y + r*(120), 100, 100)
        self.flipped = False
        self.matched = False
        self.scale = 1.0
        self.target_scale = 1.0

    def update(self):
        diff = self.target_scale - self.scale
        self.scale += diff * 0.2
        if abs(diff) < 0.05: self.scale = self.target_scale

    def flip(self):
        self.flipped = not self.flipped

    def draw(self):
        if self.matched: return
        draw_rect = pygame.Rect(0, 0, int(100 * abs(self.scale)), 100)
        draw_rect.center = self.rect.center
        
        if self.flipped:
            pygame.draw.rect(screen, (255,255,255), draw_rect, border_radius=10)
            txt = font.render(str(self.val), True, (0,0,0))
            screen.blit(txt, (draw_rect.centerx - txt.get_width()//2, draw_rect.centery - txt.get_height()//2))
        else:
            pygame.draw.rect(screen, (60,60,80), draw_rect, border_radius=10)
            pygame.draw.rect(screen, (0,255,255), draw_rect, 3, border_radius=10)

def send_score(score):
    if TOKEN:
        try: requests.post(f"{API_URL}/api/score", json={"score": score, "game_id": "memory"}, headers={"Authorization": f"Bearer {TOKEN}"})
        except: pass

def main():
    cards = [Card(v, i//4, i%4) for i, v in enumerate(list(range(8))*2)]
    random.shuffle(cards)
    
    score = 0
    state = "WAIT"
    first = None
    wait_timer = 0
    
    running = True
    while running:
        screen.fill((30, 30, 40))
        
        for p in particles[:]:
            p.update(); p.draw()
            if p.life <= 0: particles.remove(p)

        screen.blit(font.render(f"Score: {score}", True, (0,255,255)), (20, 20))

        if state == "WAIT":
            screen.blit(large_font.render("CLICK TO START", True, (50,255,50)), (130, 280))
        elif state == "OVER":
            screen.blit(large_font.render("ALL CLEARED!", True, (50,255,50)), (140, 250))
            screen.blit(font.render("Press SPACE to Exit", True, (200,200,200)), (180, 320))
        else:
            for c in cards:
                c.update(); c.draw()
            
            if state == "CHECK" and pygame.time.get_ticks() > wait_timer:
                if first.val == second.val:
                    first.matched = True; second.matched = True
                    score += 100
                    for _ in range(20): particles.append(Particle(first.rect.centerx, first.rect.centery, (50,255,50)))
                    for _ in range(20): particles.append(Particle(second.rect.centerx, second.rect.centery, (50,255,50)))
                else:
                    first.flip(); second.flip()
                    score = max(0, score - 10)
                
                first, second = None, None
                state = "PLAY"
                
                if all(c.matched for c in cards):
                    state = "OVER"
                    send_score(score)

        pygame.display.flip()
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if state == "WAIT" and event.type == pygame.MOUSEBUTTONDOWN: state = "PLAY"
            elif state == "OVER" and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE: running = False
            
            elif state == "PLAY" and event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for c in cards:
                    if c.rect.collidepoint(mx, my) and not c.flipped and not c.matched:
                        c.flip()
                        if not first: first = c
                        else:
                            second = c
                            state = "CHECK"
                            wait_timer = pygame.time.get_ticks() + 800

    pygame.quit()

if __name__ == "__main__":
    main()