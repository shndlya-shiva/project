import pygame
import sys
import random
import secrets
from pygame.locals import *

pygame.init()

# Fullscreen + display
SCREEN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
DISPLAY_W, DISPLAY_H = SCREEN.get_size()
pygame.display.set_caption("Memory Puzzle - Menu Selection")
CLOCK = pygame.time.Clock()
FPS = 60
# Colors & Fonts
BG = (240, 245, 250)
PANEL = (230, 255, 230)
CARD = (180, 220, 180)
HOVER = (200, 245, 200)
BLACK = (0, 0, 0)

TITLE_FONT = pygame.font.Font(None, 84)
SUB_FONT = pygame.font.Font(None, 44)
UI_FONT = pygame.font.Font(None, 32)

EMOJI_FONT_PATH = r"C:\Windows\Fonts\seguiemj.ttf"  
# Themes & Levels
THEMES = {
    "Fruits": ["🍎","🍌","🍇","🍉","🍒","🍍","🥝","🍑","🍋","🍐"],
    "Animals": ["🐶","🐱","🐼","🐵","🐸","🦊","🐯","🦁","🐰","🐷"],
    "Emoji":   ["😀","😁","😂","🤣","😊","😎","😍","🤩","🤖","👻"]
}

LEVELS = {
    "1 - EASY   (4x4)" : (4, 4, 60),
    "2 - MEDIUM (6x6)" : (6, 6, 50),
    "3 - HARD   (8x8)" : (8, 8, 40),
    "4 - EXTREME(10x10)": (10, 10, 35)
}

# default selections
theme_keys = list(THEMES.keys())
theme_index = 0
current_theme = theme_keys[theme_index]

# Utility helpers
def draw_center(text, y, font, color=BLACK):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(DISPLAY_W//2, y))
    SCREEN.blit(surf, rect)

def fade_in():
    s = pygame.Surface((DISPLAY_W, DISPLAY_H))
    s.fill((0,0,0))
    for a in range(255, -1, -15):
        s.set_alpha(a)
        SCREEN.blit(s, (0,0))
        pygame.display.flip()
        pygame.time.delay(8)

def safe_emoji_render(emoji, size):
    try:
        f = pygame.font.Font(EMOJI_FONT_PATH, int(size))
    except Exception:
        f = pygame.font.Font(None, int(size))
    return f.render(emoji, True, (0,0,0))

# Menu screen (theme + difficulty)
def menu_screen():
    global theme_index, current_theme
    fade_in()
    while True:
        SCREEN.fill(BG)
        # Title
        draw_center("🍉 MEMORY PUZZLE 🍉", 110, TITLE_FONT)

        # Theme selector area
        draw_center(f"Theme: {current_theme}   (press T to cycle themes)", 210, SUB_FONT)

        # Show a sample row of icons from current theme
        sample = THEMES[current_theme][:6]
        start_x = DISPLAY_W//2 - (len(sample)*60)//2
        y_icons = 270
        for i, ic in enumerate(sample):
            surf = safe_emoji_render(ic, 48)
            rect = surf.get_rect(center=(start_x + i*60 + 30, y_icons))
            SCREEN.blit(surf, rect)

        # Difficulty list - press 1..4 to start that difficulty
        y0 = 360
        draw_center("Choose difficulty (press 1 - 4 to start):", y0, UI_FONT)
        idx = 1
        for label in LEVELS.keys():
            text = f"{label}"
            draw_center(text, y0 + 40*idx, UI_FONT, color=(0,50,0) if idx==1 else BLACK)
            idx += 1

        # Instructions
        draw_center("ESC = Quit   |   Press 1/2/3/4 to start with selected difficulty", DISPLAY_H - 80, UI_FONT)

        pygame.display.update()

        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit(); sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    # exit fullscreen and quit
                    pygame.display.set_mode((DISPLAY_W, DISPLAY_H))
                    pygame.quit(); sys.exit()
                if e.key == K_t:
                    theme_index = (theme_index + 1) % len(theme_keys)
                    current_theme = theme_keys[theme_index]
                if e.key in (K_1, K_2, K_3, K_4):
                    # map key to level entry and start immediately
                    level_num = {K_1:1, K_2:2, K_3:3, K_4:4}[e.key]
                    level_label = list(LEVELS.keys())[level_num-1]
                    W, H, time_s = LEVELS[level_label]
                    return current_theme, level_label, W, H, time_s

        CLOCK.tick(FPS)

# Board helpers & play
def compute_box_and_gap(W, H):
    GAP = 10
    max_w = DISPLAY_W * 0.80
    max_h = DISPLAY_H * 0.75
    box_w = (max_w - (W-1)*GAP)/W
    box_h = (max_h - (H-1)*GAP)/H
    return max(30, int(min(box_w, box_h))), GAP

def generate_board(W, H, theme):
    needed = (W*H)//2
    pool = THEMES[theme].copy()
    # ensure enough items
    while len(pool) < needed:
        pool += pool
    rand = secrets.SystemRandom()
    rand.shuffle(pool)
    icons = pool[:needed]*2
    rand.shuffle(icons)
    board = []
    idx = 0
    for x in range(W):
        col = []
        for y in range(H):
            col.append(icons[idx]); idx += 1
        board.append(col)
    return board

def get_start_pos(W, H, BOX, GAP):
    total_w = W*BOX + (W-1)*GAP
    total_h = H*BOX + (H-1)*GAP
    sx = (DISPLAY_W - total_w)//2
    sy = (DISPLAY_H - total_h)//2
    return sx, sy

def play_level(theme, level_label, W, H, time_seconds):
    BOX, GAP = compute_box_and_gap(W, H)
    sx, sy = get_start_pos(W, H, BOX, GAP)
    board = generate_board(W, H, theme)
    revealed = [[False]*H for _ in range(W)]
    first = None
    matches = 0
    total_pairs = (W*H)//2

    # initial brief reveal
    reveal_all = True
    reveal_start = pygame.time.get_ticks()

    # timer (ms)
    time_left_ms = time_seconds * 1000
    start_ticks = pygame.time.get_ticks()

    # emoji font cache small
    emoji_cache = {}

    def emoji_surf(e, size):
        key = (e, size)
        if key in emoji_cache:
            return emoji_cache[key]
        try:
            f = pygame.font.Font(EMOJI_FONT_PATH, int(size))
        except Exception:
            f = pygame.font.Font(None, int(size))
        s = f.render(e, True, (0,0,0))
        emoji_cache[key] = s
        return s

    # fade-in before play
    fade = pygame.Surface((DISPLAY_W, DISPLAY_H))
    fade.fill((0,0,0))
    for a in range(200, -1, -20):
        SCREEN.fill(BG)
        fade.set_alpha(a)
        SCREEN.blit(fade, (0,0))
        pygame.display.flip()
        pygame.time.delay(10)

    while True:
        dt = CLOCK.tick(FPS)
        # update time
        elapsed = pygame.time.get_ticks() - start_ticks
        remaining_ms = max(0, time_left_ms - elapsed)
        if remaining_ms == 0:
            return False, 0  # time up -> lose

        SCREEN.fill(BG)
        # header
        draw_center = lambda txt, yy, f=UI_FONT: SCREEN.blit(f.render(txt, True, BLACK), f.render(txt, True, BLACK).get_rect(center=(DISPLAY_W//2, yy)))
        # show level & timer
        SCREEN.blit(SUB_FONT.render(f"{level_label}  -  Theme: {theme}", True, BLACK), (30,30))
        SCREEN.blit(UI_FONT.render(f"Time: {remaining_ms//1000}s   (ESC to Quit)", True, BLACK), (30,80))

        # draw board
        mx, my = pygame.mouse.get_pos()
        for x in range(W):
            for y in range(H):
                left = sx + x*(BOX+GAP)
                top  = sy + y*(BOX+GAP)
                rect = pygame.Rect(left, top, BOX, BOX)
                hovering = rect.collidepoint(mx, my)
                if revealed[x][y] or reveal_all:
                    pygame.draw.rect(SCREEN, (255,255,255), rect, border_radius=8)
                    surf = emoji_surf(board[x][y], BOX*0.65)
                    srect = surf.get_rect(center=rect.center)
                    SCREEN.blit(surf, srect)
                else:
                    pygame.draw.rect(SCREEN, HOVER if hovering else CARD, rect, border_radius=8)
                pygame.draw.rect(SCREEN, (120,120,120), rect, 2, border_radius=8)

        # stop initial reveal after 1.1s
        if reveal_all and pygame.time.get_ticks() - reveal_start > 1100:
            reveal_all = False

        pygame.display.update()

        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit(); sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    # exit fullscreen and quit safely
                    pygame.display.set_mode((DISPLAY_W, DISPLAY_H))
                    pygame.quit(); sys.exit()
            if e.type == MOUSEBUTTONUP and not reveal_all:
                px, py = e.pos
                bx, by = None, None
                for ix in range(W):
                    for iy in range(H):
                        rleft = sx + ix*(BOX+GAP)
                        rtop  = sy + iy*(BOX+GAP)
                        r = pygame.Rect(rleft, rtop, BOX, BOX)
                        if r.collidepoint(px, py):
                            bx, by = ix, iy
                if bx is not None and not revealed[bx][by]:
                    revealed[bx][by] = True
                    if first is None:
                        first = (bx, by)
                    else:
                        fx, fy = first
                        if board[fx][fy] == board[bx][by]:
                            matches += 1
                        else:
                            pygame.display.update()
                            pygame.time.wait(550)
                            revealed[fx][fy] = False
                            revealed[bx][by] = False
                        first = None

        if matches == total_pairs:
            return True, remaining_ms//1000

# Win / Lose screens
def win_screen(remaining_s):
    SCREEN.fill((220, 255, 220))
    draw_center_text = lambda txt,y,f=TITLE_FONT: SCREEN.blit(f.render(txt, True, BLACK), f.render(txt, True, BLACK).get_rect(center=(DISPLAY_W//2, y)))
    draw_center_text("🎉 LEVEL CLEARED! 🎉", DISPLAY_H//2 - 40)
    draw_center_text(f"Time left: {remaining_s}s", DISPLAY_H//2 + 40, SUB_FONT)
    pygame.display.update()
    pygame.time.wait(1200)

def lose_screen():
    SCREEN.fill((255, 220, 220))
    draw_center_text = lambda txt,y,f=TITLE_FONT: SCREEN.blit(f.render(txt, True, BLACK), f.render(txt, True, BLACK).get_rect(center=(DISPLAY_W//2, y)))
    draw_center_text("⛔ TIME'S UP ⛔", DISPLAY_H//2 - 40)
    draw_center_text("Press ENTER to return to menu", DISPLAY_H//2 + 40, SUB_FONT)
    pygame.display.update()
    waiting = True
    while waiting:
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit(); sys.exit()
            if e.type == KEYDOWN and e.key == K_RETURN:
                waiting = False
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                pygame.display.set_mode((DISPLAY_W, DISPLAY_H))
                pygame.quit(); sys.exit()

# Main
def main():
    while True:
        theme, level_label, W, H, tsec = menu_screen()
        success, remaining = play_level(theme, level_label, W, H, tsec)
        if success:
            win_screen(remaining)
        else:
            lose_screen()

if __name__ == "__main__":
    main()
