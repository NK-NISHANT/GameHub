import pygame, sys, random, requests

API_URL = "http://127.0.0.1:5000"
TOKEN, USERNAME = None, "Guest"
if len(sys.argv) > 2: TOKEN, USERNAME = sys.argv[1], sys.argv[2]

pygame.init()
WIDTH, HEIGHT = 600, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"Neon Snake | {USERNAME}")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 24, bold=True)
large_font = pygame.font.SysFont("Arial", 50, bold=True)
CELL = 20

def send_score(score):
    if TOKEN:
        try: requests.post(f"{API_URL}/api/score", json={"score": score, "game_id": "snake"}, headers={"Authorization": f"Bearer {TOKEN}"})
        except: pass

def main():
    snake = [(100, 100), (80, 100), (60, 100)]
    direction = (CELL, 0)
    food = (random.randrange(0, WIDTH, CELL), random.randrange(0, HEIGHT, CELL))
    score = 0
    state = "WAIT"
    
    running = True
    while running:
        screen.fill((15, 15, 20))
        
        # Grid
        for x in range(0, WIDTH, CELL): pygame.draw.line(screen, (30,30,40), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, CELL): pygame.draw.line(screen, (30,30,40), (0, y), (WIDTH, y))
        
        if state == "WAIT":
            txt = large_font.render("PRESS ARROW TO START", True, (255,255,255))
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2))
            st = font.render(f"Logged in as: {USERNAME}", True, (100, 200, 255))
            screen.blit(st, (WIDTH//2 - st.get_width()//2, HEIGHT//2 + 50))
            
        elif state == "PLAY":
            new_head = (snake[0][0] + direction[0], snake[0][1] + direction[1])
            
            if (new_head[0] < 0 or new_head[0] >= WIDTH or 
                new_head[1] < 0 or new_head[1] >= HEIGHT or new_head in snake):
                send_score(score)
                state = "OVER"
            else:
                snake.insert(0, new_head)
                if abs(new_head[0] - food[0]) < CELL and abs(new_head[1] - food[1]) < CELL:
                    score += 10
                    food = (random.randrange(0, WIDTH, CELL), random.randrange(0, HEIGHT, CELL))
                else:
                    snake.pop()

            pygame.draw.rect(screen, (255, 50, 100), (*food, CELL, CELL), border_radius=5)
            for i, s in enumerate(snake):
                col = (0, 255, 150) if i == 0 else (0, 200, 100)
                pygame.draw.rect(screen, col, (*s, CELL, CELL), border_radius=4)
                
            screen.blit(font.render(f"Score: {score}", True, (255,255,255)), (10, 10))

        elif state == "OVER":
            pygame.draw.rect(screen, (0,0,0), (WIDTH//2-150, HEIGHT//2-100, 300, 200), border_radius=10)
            pygame.draw.rect(screen, (255,0,0), (WIDTH//2-150, HEIGHT//2-100, 300, 200), 2, border_radius=10)
            
            t1 = large_font.render("GAME OVER", True, (255, 50, 50))
            t2 = font.render(f"Final Score: {score}", True, (255,255,255))
            t3 = font.render("Press SPACE to Close", True, (150, 150, 150))
            
            screen.blit(t1, (WIDTH//2 - t1.get_width()//2, HEIGHT//2 - 60))
            screen.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2))
            screen.blit(t3, (WIDTH//2 - t3.get_width()//2, HEIGHT//2 + 50))

        pygame.display.flip()
        clock.tick(10 if state == "PLAY" else 60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if state == "WAIT":
                    state = "PLAY"
                    if event.key == pygame.K_UP: direction = (0, -CELL)
                    elif event.key == pygame.K_DOWN: direction = (0, CELL)
                    elif event.key == pygame.K_LEFT: direction = (-CELL, 0)
                    elif event.key == pygame.K_RIGHT: direction = (CELL, 0)
                elif state == "PLAY":
                    if event.key == pygame.K_UP and direction != (0, CELL): direction = (0, -CELL)
                    elif event.key == pygame.K_DOWN and direction != (0, -CELL): direction = (0, CELL)
                    elif event.key == pygame.K_LEFT and direction != (CELL, 0): direction = (-CELL, 0)
                    elif event.key == pygame.K_RIGHT and direction != (-CELL, 0): direction = (CELL, 0)
                elif state == "OVER":
                    if event.key == pygame.K_SPACE: running = False

    pygame.quit()

if __name__ == "__main__":
    main()