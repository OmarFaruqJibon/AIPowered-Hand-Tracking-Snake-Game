# main.py
import pygame
import cv2
import numpy as np
from game import SnakeGame
from hand_tracker import HandTracker, CAM_W, CAM_H

CELL_SIZE = 24
GRID_W = 28
GRID_H = 21
FPS = 3
PREVIEW_W, PREVIEW_H = 200, 150

# Colors
BLACK = (6,6,10)
WHITE = (240,240,240)
RED = (255,60,80)
GREEN = (50,230,90)
GRAY = (40,40,55)
BLUE = (70,120,255)
YELLOW = (255,230,100)
NEON_PINK = (255,64,200)

# Sound generator (tiny utility)
def make_sound(freq=440, duration_ms=120, volume=0.2, sample_rate=44100):
    t = np.linspace(0, duration_ms / 1000, int(sample_rate * duration_ms / 1000), False)
    wave = 0.5 * np.sin(2 * np.pi * freq * t)
    audio = np.int16(wave * 32767 * volume)
    sound = pygame.mixer.Sound(buffer=audio.tobytes())
    return sound

# Neon/glow helper
def draw_glow_rect(surface, rect, color, glow_radius=8):
    x, y, w, h = rect
    glow = pygame.Surface((w + glow_radius*2, h + glow_radius*2), pygame.SRCALPHA)
    for i in range(glow_radius, 0, -1):
        alpha = int(10 + (i / glow_radius) * 40)
        pygame.draw.rect(glow, (*color, alpha), (glow_radius - i, glow_radius - i, w + 2*i, h + 2*i), border_radius=8)
    surface.blit(glow, (x - glow_radius, y - glow_radius), special_flags=pygame.BLEND_ADD)

def neon_text(surface, text, font, pos, neon_color, outline=3):
    x, y = pos
    # outline - draw darker layers for glow effect
    for dx, dy in [(-outline,0),(outline,0),(0,-outline),(0,outline)]:
        img = font.render(text, True, (10,10,10))
        surface.blit(img, (x+dx, y+dy))
    txt = font.render(text, True, neon_color)
    surface.blit(txt, (x, y))

# Button class
class Button:
    def __init__(self, rect, label, font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font = font
        self.hover = False

    def draw(self, surface):
        color = NEON_PINK if self.hover else BLUE
        draw_glow_rect(surface, self.rect, color, glow_radius=8)
        # inner rect
        inner = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        inner.fill((20,20,30,220))
        surface.blit(inner, (self.rect.x, self.rect.y))
        # label
        txt = self.font.render(self.label, True, (230,230,230))
        surface.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery - txt.get_height()//2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

def main():
    pygame.init()
    pygame.mixer.init()
    screen_w = GRID_W * CELL_SIZE + 260
    screen_h = GRID_H * CELL_SIZE
    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("Hand Controlled Snake Game")

    font_big = pygame.font.SysFont("dejavusans", 44)
    font_med = pygame.font.SysFont("dejavusans", 20)
    font_small = pygame.font.SysFont("dejavusans", 16)
    clock = pygame.time.Clock()

    # sounds
    s_eat = make_sound(freq=880, duration_ms=120, volume=0.12)
    s_click = make_sound(freq=600, duration_ms=80, volume=0.12)
    s_pause = make_sound(freq=220, duration_ms=160, volume=0.10)
    s_resume = make_sound(freq=440, duration_ms=120, volume=0.10)
    s_over = make_sound(freq=120, duration_ms=300, volume=0.16)

    tracker = HandTracker()
    game = SnakeGame(GRID_W, GRID_H, CELL_SIZE)

    # SIDE PANEL LAYOUT
    panel_x = GRID_W * CELL_SIZE + 20

    # Score at top
    score_y = 20

    # Buttons horizontal configuration
    BUTTON_W, BUTTON_H = 65, 40
    BUTTON_SPACING = 12
    total_buttons_width = BUTTON_W * 3 + BUTTON_SPACING * 2
    buttons_start_x = panel_x  
    
    panel_width = 220
    buttons_start_x = panel_x + max(0, (panel_width - total_buttons_width) // 2)

    btn_y = score_y + 80
    btn_new   = Button((buttons_start_x, btn_y, BUTTON_W, BUTTON_H), "New", font_med)
    btn_pause = Button((buttons_start_x + (BUTTON_W + BUTTON_SPACING), btn_y, BUTTON_W, BUTTON_H), "Pause", font_med)
    btn_exit  = Button((buttons_start_x + 2*(BUTTON_W + BUTTON_SPACING), btn_y, BUTTON_W, BUTTON_H), "Exit", font_med)

    # short instructions (below buttons)
    inst_y = btn_y + BUTTON_H + 16
    instructions = [
        "Raise index finger to move",
        "Use buttons for Pause & New Game",
        "Esc = Exit"
    ]

    # debug / thresholds
    zone_thresholds = (0.35, 0.65, 0.35, 0.65)  # left,right,top,bottom (fractions)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_n:
                    game.reset()
                    s_click.play()
                if event.key == pygame.K_p:
                    game.paused = not game.paused
                    (s_pause if game.paused else s_resume).play()

            # handle button events (clicks + hover)
            if btn_new.handle_event(event):
                game.reset()
                s_click.play()
            if btn_pause.handle_event(event):
                game.paused = not game.paused
                (s_pause if game.paused else s_resume).play()
            if btn_exit.handle_event(event):
                running = False

        # read camera & hand
        frame, hands = tracker.read_frame()
        if frame is None:
            break
        index_pos, _ = tracker.get_index_and_fingers(hands)  # ignore finger count entirely

        requested_dir = None
        if index_pos is not None and not game.game_over and not game.paused:
            ix, iy = index_pos
            left_th = CAM_W * zone_thresholds[0]
            right_th = CAM_W * zone_thresholds[1]
            top_th = CAM_H * zone_thresholds[2]
            bottom_th = CAM_H * zone_thresholds[3]

            # prefer horizontal movement if pointer is strongly left/right
            if ix < left_th:
                requested_dir = (-1, 0)
            elif ix > right_th:
                requested_dir = (1, 0)
            elif iy < top_th:
                requested_dir = (0, -1)
            elif iy > bottom_th:
                requested_dir = (0, 1)

            if requested_dir:
                game.dir = game.clamp_dir(requested_dir)

        # advance game
        prev_score = game.score
        game.step()
        if game.score != prev_score:
            s_eat.play()
        if game.game_over:
            s_over.play()

        # draw background
        screen.fill(BLACK)

        # draw grid + snake + food (game area)
        area_surf = pygame.Surface((GRID_W*CELL_SIZE, GRID_H*CELL_SIZE))
        area_surf.fill((10,10,14))

        # grid lines subtle
        for x in range(GRID_W):
            pygame.draw.line(area_surf, (18,18,26), (x*CELL_SIZE, 0), (x*CELL_SIZE, GRID_H*CELL_SIZE))
        for y in range(GRID_H):
            pygame.draw.line(area_surf, (18,18,26), (0, y*CELL_SIZE), (GRID_W*CELL_SIZE, y*CELL_SIZE))

        # food
        if game.food:
            fx, fy = game.food
            pygame.draw.rect(area_surf, RED, (fx*CELL_SIZE+2, fy*CELL_SIZE+2, CELL_SIZE-4, CELL_SIZE-4), border_radius=6)

        # snake
        for i, (sx, sy) in enumerate(game.snake):
            color = (120,200,255) if i == 0 else (80,255,140)
            pygame.draw.rect(area_surf, color, (sx*CELL_SIZE+2, sy*CELL_SIZE+2, CELL_SIZE-4, CELL_SIZE-4), border_radius=6)
            # slight inner glow for head
            if i == 0:
                pygame.draw.rect(area_surf, (230,230,255,30), (sx*CELL_SIZE+2, sy*CELL_SIZE+2, CELL_SIZE-4, CELL_SIZE-4), border_radius=6)

        # blit game area
        screen.blit(area_surf, (0,0))

        # RIGHT PANEL (neon UI)
        panel_x = GRID_W * CELL_SIZE + 20

        # Score panel (top)
        score_rect = (panel_x, score_y, 220, 64)
        draw_glow_rect(screen, score_rect, (120,255,200), glow_radius=3)
        pygame.draw.rect(screen, (18,18,26), score_rect, border_radius=5)
        score_text = f"Score: {game.score}"
        screen.blit(font_big.render(score_text, True, (240,240,240)), (panel_x + 12, score_y + 18))


        # Draw buttons (horizontal)
        btn_new.draw(screen)
        btn_pause.draw(screen)
        btn_exit.draw(screen)

        # short instructions 
        for i, line in enumerate(instructions):
            screen.blit(font_small.render(line, True, (200,200,200)), (panel_x, inst_y + i*18))

        # camera preview (bottom)
        preview = cv2.resize(frame, (PREVIEW_W, PREVIEW_H))
        preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
        surf = pygame.image.frombuffer(preview.tobytes(), (PREVIEW_W, PREVIEW_H), "RGB")
        px = panel_x
        py = screen_h - PREVIEW_H - 16
        screen.blit(surf, (px, py))
        pygame.draw.rect(screen, (30,30,40), (px-2, py-2, PREVIEW_W+4, PREVIEW_H+4), 2)

        # draw index dot in preview
        if index_pos:
            ix, iy = index_pos
            dx = int((ix / CAM_W) * PREVIEW_W)
            dy = int((iy / CAM_H) * PREVIEW_H)
            pygame.draw.circle(screen, YELLOW, (px + dx, py + dy), 5)

        # pause overlay
        if game.paused:
            overlay = pygame.Surface((GRID_W*CELL_SIZE, GRID_H*CELL_SIZE), pygame.SRCALPHA)
            overlay.fill((8, 12, 18, 180))
            screen.blit(overlay, (0,0))
            neon_text(screen, "PAUSED", font_big, (GRID_W*CELL_SIZE//2 - 80, GRID_H*CELL_SIZE//2 - 22), (200,240,255), outline=3)

        pygame.display.flip()
        clock.tick(FPS)

    tracker.release()
    pygame.quit()

if __name__ == "__main__":
    main()
