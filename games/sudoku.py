import pygame, sys, requests, random, copy

API_URL = "http://127.0.0.1:5000"
TOKEN, USERNAME = None, "Guest"
if len(sys.argv) > 2:
    TOKEN, USERNAME = sys.argv[1], sys.argv[2]

pygame.init()
WIDTH, HEIGHT = 540, 680
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"Sudoku Master | {USERNAME}")
clock = pygame.time.Clock()

# Fonts
font = pygame.font.SysFont("Arial", 40)
pencil_font = pygame.font.SysFont("Arial", 14)
ui_font = pygame.font.SysFont("Arial", 20)
title_font = pygame.font.SysFont("Arial", 50, bold=True)

# State
state = "MENU"
grid, solution, original, notes = [], [], [], {}
selected, mistakes, difficulty, score = None, 0, "Medium", 0
completed_sections, highlights = set(), []

def send_score(final_score):
    if TOKEN:
        try:
            requests.post(f"{API_URL}/api/score", json={"score": final_score, "game_id": "sudoku"}, headers={"Authorization": f"Bearer {TOKEN}"})
        except: pass

def is_valid(board, r, c, num):
    for i in range(9):
        if board[r][i] == num and i != c: return False
        if board[i][c] == num and i != r: return False
    br, bc = (r//3)*3, (c//3)*3
    for i in range(3):
        for j in range(3):
            if board[br+i][bc+j] == num and (br+i, bc+j) != (r,c): return False
    return True

def solve_board(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                nums = list(range(1, 10))
                random.shuffle(nums)
                for n in nums:
                    if is_valid(board, r, c, n):
                        board[r][c] = n
                        if solve_board(board): return True
                        board[r][c] = 0
                return False
    return True

def generate_new_game(diff_level):
    board = [[0]*9 for _ in range(9)]
    solve_board(board)
    sol = copy.deepcopy(board)
    
    if diff_level == "Easy": count = 30
    elif diff_level == "Medium": count = 40
    else: count = 52
    
    attempts = count
    while attempts > 0:
        r, c = random.randint(0,8), random.randint(0,8)
        if board[r][c] != 0:
            board[r][c] = 0
            attempts -= 1
    return board, sol

def check_completions():
    global score
    # Check Rows
    for r in range(9):
        if f"row_{r}" not in completed_sections:
            if 0 not in grid[r] and len(set(grid[r])) == 9:
                completed_sections.add(f"row_{r}")
                score += 100
                highlights.append([pygame.Rect(0, r*60, 540, 60), 30])

    # Check Cols
    for c in range(9):
        if f"col_{c}" not in completed_sections:
            col_vals = [grid[r][c] for r in range(9)]
            if 0 not in col_vals and len(set(col_vals)) == 9:
                completed_sections.add(f"col_{c}")
                score += 100
                highlights.append([pygame.Rect(c*60, 0, 60, 540), 30])

    # Check Boxes
    for br in range(3):
        for bc in range(3):
            if f"box_{br}_{bc}" not in completed_sections:
                vals = []
                for i in range(3):
                    for j in range(3):
                        vals.append(grid[br*3+i][bc*3+j])
                if 0 not in vals and len(set(vals)) == 9:
                    completed_sections.add(f"box_{br}_{bc}")
                    score += 100
                    highlights.append([pygame.Rect(bc*180, br*180, 180, 180), 30])

def draw_grid():
    # Highlights
    for h in highlights:
        s = pygame.Surface((h[0].w, h[0].h))
        s.set_alpha(100)
        s.fill((100, 255, 100))
        screen.blit(s, (h[0].x, h[0].y))
        h[1] -= 1
    highlights[:] = [h for h in highlights if h[1] > 0]

    # Selection
    if selected:
        pygame.draw.rect(screen, (200, 230, 255), (selected[1]*60, selected[0]*60, 60, 60))

    # Numbers
    for r in range(9):
        for c in range(9):
            val = grid[r][c]
            if val != 0:
                col = (0,0,0) if original[r][c] != 0 else ((50,50,255) if val == solution[r][c] else (220,0,0))
                screen.blit(font.render(str(val), True, col), (c*60 + 20, r*60 + 10))
            elif (r,c) in notes:
                for n in notes[(r,c)]:
                    nx = c*60 + 5 + ((n-1)%3)*18
                    ny = r*60 + 2 + ((n-1)//3)*18
                    screen.blit(pencil_font.render(str(n), True, (100,100,100)), (nx, ny))

    # Lines
    for i in range(10):
        thick = 4 if i % 3 == 0 else 1
        pygame.draw.line(screen, (0,0,0), (0, i*60), (540, i*60), thick)
        pygame.draw.line(screen, (0,0,0), (i*60, 0), (i*60, 540), thick)

def draw_ui():
    pygame.draw.rect(screen, (240, 240, 250), (0, 542, WIDTH, HEIGHT-542))
    pygame.draw.line(screen, (0,0,0), (0, 542), (WIDTH, 542), 3)
    
    if state == "MENU":
        screen.blit(title_font.render("SUDOKU", True, (0,0,0)), (150, 200))
        screen.blit(ui_font.render("1: Easy | 2: Medium | 3: Hard", True, (0,100,0)), (130, 300))
    elif state == "PLAY":
        screen.blit(ui_font.render(f"Score: {score}  |  Mistakes: {mistakes}/3", True, (50,50,50)), (20, 560))
        screen.blit(ui_font.render("Num: Fill  |  Shift+Num: Pencil Note", True, (100,100,100)), (20, 600))
    elif state == "GAMEOVER":
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0,0,0,150))
        screen.blit(s, (0,0))
        pygame.draw.rect(screen, (255,255,255), (70, 200, 400, 220), border_radius=10)
        screen.blit(title_font.render("GAME OVER", True, (220,0,0)), (110, 220))
        screen.blit(ui_font.render(f"Final Score: {score}", True, (0,0,0)), (180, 280))
        screen.blit(ui_font.render("Press 'R' to Retry | 'S' for Solution", True, (50,50,255)), (90, 360))
    elif state == "GAMEOVER_VIEW":
        screen.blit(ui_font.render("SOLUTION SHOWN. Press 'R' to Menu", True, (200,0,0)), (20, 560))
    elif state == "WIN":
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0,0,0,150))
        screen.blit(s, (0,0))
        pygame.draw.rect(screen, (255,255,255), (70, 200, 400, 200), border_radius=10)
        screen.blit(title_font.render("SOLVED!", True, (0,200,0)), (150, 220))
        screen.blit(ui_font.render(f"Score: {score} Uploaded!", True, (0,0,0)), (150, 290))
        screen.blit(ui_font.render("Press 'R' to Play Again", True, (50,50,255)), (150, 340))

def main():
    global state, grid, solution, original, selected, mistakes, difficulty, notes, score, completed_sections
    running = True
    while running:
        screen.fill((255,255,255))
        if state == "MENU": draw_ui()
        else:
            draw_grid()
            draw_ui()

        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if state == "MENU" and event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                    if event.key == pygame.K_1: difficulty = "Easy"
                    elif event.key == pygame.K_2: difficulty = "Medium"
                    else: difficulty = "Hard"
                    grid, solution = generate_new_game(difficulty)
                    original = copy.deepcopy(grid)
                    notes = {}
                    mistakes = 0
                    score = 0
                    selected = (0,0)
                    completed_sections = set()
                    state = "PLAY"

            elif state == "PLAY":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if pygame.mouse.get_pos()[1] < 540:
                        selected = (pygame.mouse.get_pos()[1]//60, pygame.mouse.get_pos()[0]//60)
                
                if event.type == pygame.KEYDOWN and selected:
                    r, c = selected
                    if event.key == pygame.K_UP: selected = (max(0,r-1), c)
                    elif event.key == pygame.K_DOWN: selected = (min(8,r+1), c)
                    elif event.key == pygame.K_LEFT: selected = (r, max(0,c-1))
                    elif event.key == pygame.K_RIGHT: selected = (r, min(8,c+1))
                    
                    elif original[r][c] == 0:
                        num = -1
                        # Map keys 1-9
                        if 49 <= event.key <= 57: num = event.key - 48
                        elif event.key == pygame.K_BACKSPACE: num = 0
                        
                        if num != -1:
                            # Pencil Mode (Shift)
                            if num > 0 and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                                if (r,c) not in notes: notes[(r,c)] = []
                                if num in notes[(r,c)]: notes[(r,c)].remove(num)
                                else: notes[(r,c)].append(num)
                            else:
                                grid[r][c] = num
                                if (r,c) in notes: del notes[(r,c)]
                                
                                if num != 0:
                                    if num != solution[r][c]:
                                        mistakes += 1
                                        if mistakes >= 3:
                                            send_score(score)
                                            state = "GAMEOVER"
                                    else:
                                        check_completions()
                                        if grid == solution:
                                            score += 500
                                            send_score(score)
                                            state = "WIN"

            elif state in ["GAMEOVER", "WIN", "GAMEOVER_VIEW"] and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: state = "MENU"
                elif event.key == pygame.K_s and state == "GAMEOVER":
                    grid = copy.deepcopy(solution)
                    state = "GAMEOVER_VIEW"

    pygame.quit()

if __name__ == "__main__":
    main()