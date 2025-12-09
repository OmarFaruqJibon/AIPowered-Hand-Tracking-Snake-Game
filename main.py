# main.py
import pygame
import cv2
import numpy as np
from game import SnakeGame
from hand_tracker import HandTracker, CAM_W, CAM_H

CELL_SIZE = 24
GRID_W = 28
GRID_H = 21
FPS = 7 
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

# Sound generator
def make_sound(freq=440, duration_ms=120, volume=0.2, sample_rate=44100):
    t = np.linspace(0, duration_ms / 1000, int(sample_rate * duration_ms / 1000), False)
    wave = 0.5 * np.sin(2 * np.pi * freq * t)
    audio = np.int16(wave * 32767 * volume)
    sound = pygame.mixer.Sound(buffer=audio.tobytes())
    return sound

glow_cache = {}

def draw_glow_rect(surface, rect, color, glow_radius=8):
    key = (rect[2], rect[3], color)
    if key not in glow_cache:
        w, h = rect[2], rect[3]
        glow = pygame.Surface((w + glow_radius*2, h + glow_radius*2), pygame.SRCALPHA)
        for i in range(glow_radius, 0, -1):
            alpha = int(10 + (i / glow_radius) * 40)
            pygame.draw.rect(glow, (*color, alpha), (glow_radius - i, glow_radius - i, w + 2*i, h + 2*i), border_radius=8)
        glow_cache[key] = glow
    surface.blit(glow_cache[key], (rect[0]-glow_radius, rect[1]-glow_radius), special_flags=pygame.BLEND_ADD)

def neon_text(surface, text, font, pos, neon_color, outline=3):
    x, y = pos
    for dx, dy in [(-outline,0),(outline,0),(0,-outline),(0,outline)]:
        img = font.render(text, True, (10,10,10))
        surface.blit(img, (x+dx, y+dy))
    txt = font.render(text, True, neon_color)
    surface.blit(txt, (x, y))

# Button class unchanged
class Button:
    def __init__(self, rect, label, font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font = font
        self.hover = False

    def draw(self, surface):
        color = NEON_PINK if self.hover else BLUE
        draw_glow_rect(surface, self.rect, color, glow_radius=8)
        inner = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        inner.fill((20,20,30,220))
        surface.blit(inner, (self.rect.x, self.rect.y))
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

    s_eat = make_sound(freq=880, duration_ms=120, volume=0.12)
    s_click = make_sound(freq=600, duration_ms=80, volume=0.12)
    s_pause = make_sound(freq=220, duration_ms=160, volume=0.10)
    s_resume = make_sound(freq=440, duration_ms=120, volume=0.10)
    s_over = make_sound(freq=120, duration_ms=300, volume=0.16)

    tracker = HandTracker()
    game = SnakeGame(GRID_W, GRID_H, CELL_SIZE)

    panel_x = GRID_W * CELL_SIZE + 20
    score_y = 20

    BUTTON_W, BUTTON_H = 65, 40
    BUTTON_SPACING = 12
    total_buttons_width = BUTTON_W * 3 + BUTTON_SPACING * 2
    buttons_start_x = panel_x + max(0, (240 - total_buttons_width) // 2)

    btn_y = score_y + 80
    btn_new   = Button((buttons_start_x, btn_y, BUTTON_W, BUTTON_H), "New", font_med)
    btn_pause = Button((buttons_start_x + (BUTTON_W + BUTTON_SPACING), btn_y, BUTTON_W, BUTTON_H), "Pause", font_med)
    btn_exit  = Button((buttons_start_x + 2*(BUTTON_W + BUTTON_SPACING), btn_y, BUTTON_W, BUTTON_H), "Exit", font_med)

    inst_y = btn_y + BUTTON_H + 16
    instructions = [
        "Point with index finger to move",
        "Only 1 finger up = control",
        "Esc = Exit"
    ]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_n:
                    game.reset()
                    s_click.play()
                if event.key == pygame.K_p:
                    game.paused = not game.paused
                    (s_pause if game.paused else s_resume).play()

            if btn_new.handle_event(event):
                game.reset()
                s_click.play()
            if btn_pause.handle_event(event):
                game.paused = not game.paused
                (s_pause if game.paused else s_resume).play()
            if btn_exit.handle_event(event):
                running = False

        frame, hands = tracker.read_frame()
        if frame is None:
            continue

        index_pos, fingers_up = tracker.get_index_and_fingers(hands)

        # === IMPROVED DIRECTION CONTROL ===
        if (index_pos is not None and fingers_up == 1 and 
            not game.game_over and not game.paused):

            ix, iy = index_pos
            cx, cy = CAM_W // 2, CAM_H // 2
            dx = ix - cx
            dy = iy - cy

            threshold = 70  # pixels from center to trigger direction

            if abs(dx) > threshold or abs(dy) > threshold:
                if abs(dx) > abs(dy):
                    new_dir = (-1, 0) if dx < 0 else (1, 0)
                else:
                    new_dir = (0, -1) if dy < 0 else (0, 1)

                # Prevent reverse
                if new_dir != (-game.dir[0], -game.dir[1]):
                    game.dir = new_dir

        prev_score = game.score
        game.step()
        if game.score != prev_score:
            s_eat.play()
        if game.game_over and prev_score == game.score:
            s_over.play()

        screen.fill(BLACK)

        area_surf = pygame.Surface((GRID_W*CELL_SIZE, GRID_H*CELL_SIZE))
        area_surf.fill((10,10,14))

        for x in range(GRID_W):
            pygame.draw.line(area_surf, (18,18,26), (x*CELL_SIZE, 0), (x*CELL_SIZE, GRID_H*CELL_SIZE))
        for y in range(GRID_H):
            pygame.draw.line(area_surf, (18,18,26), (0, y*CELL_SIZE), (GRID_W*CELL_SIZE, y*CELL_SIZE))

        if game.food:
            fx, fy = game.food
            pygame.draw.rect(area_surf, RED, (fx*CELL_SIZE+2, fy*CELL_SIZE+2, CELL_SIZE-4, CELL_SIZE-4), border_radius=6)

        for i, (sx, sy) in enumerate(game.snake):
            color = (120,200,255) if i == 0 else (80,255,140)
            pygame.draw.rect(area_surf, color, (sx*CELL_SIZE+2, sy*CELL_SIZE+2, CELL_SIZE-4, CELL_SIZE-4), border_radius=6)
            if i == 0:
                pygame.draw.rect(area_surf, (230,230,255,30), (sx*CELL_SIZE+2, sy*CELL_SIZE+2, CELL_SIZE-4, CELL_SIZE-4), border_radius=6)

        screen.blit(area_surf, (0,0))

        # Score
        score_rect = (panel_x, score_y, 220, 64)
        draw_glow_rect(screen, score_rect, (120,255,200), glow_radius=3)
        pygame.draw.rect(screen, (18,18,26), score_rect, border_radius=5)
        screen.blit(font_big.render(f"Score: {game.score}", True, (240,240,240)), (panel_x + 12, score_y + 18))

     

        btn_new.draw(screen)
        btn_pause.draw(screen)
        btn_exit.draw(screen)

        for i, line in enumerate(instructions):
            screen.blit(font_small.render(line, True, (200,200,200)), (panel_x, inst_y + i*18))

        # Preview
        preview = cv2.resize(frame, (PREVIEW_W, PREVIEW_H))
        preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
        surf = pygame.image.frombuffer(preview.tobytes(), (PREVIEW_W, PREVIEW_H), "RGB")
        px, py = panel_x, screen_h - PREVIEW_H - 16
        screen.blit(surf, (px, py))
        pygame.draw.rect(screen, (30,30,40), (px-2, py-2, PREVIEW_W+4, PREVIEW_H+4), 2)

        # Index dot
        if index_pos and fingers_up == 1:
            dx = int((index_pos[0] / CAM_W) * PREVIEW_W)
            dy = int((index_pos[1] / CAM_H) * PREVIEW_H)
            pygame.draw.circle(screen, YELLOW, (px + dx, py + dy), 6)

            # Direction arrow
            arrow_len = 30
            center = (px + PREVIEW_W//2, py + PREVIEW_H//2)
            end = (center[0] + game.dir[0] * arrow_len, center[1] + game.dir[1] * arrow_len)
            pygame.draw.line(screen, YELLOW, center, end, 4)
            pygame.draw.circle(screen, YELLOW, end, 8)

        if game.paused:
            overlay = pygame.Surface((GRID_W*CELL_SIZE, GRID_H*CELL_SIZE), pygame.SRCALPHA)
            overlay.fill((8, 12, 18, 180))
            screen.blit(overlay, (0,0))
            neon_text(screen, "PAUSED", font_big, (GRID_W*CELL_SIZE//2 - 80, GRID_H*CELL_SIZE//2 - 22), (200,240,255))

        pygame.display.flip()
        clock.tick(FPS)

    tracker.release()
    pygame.quit()

if __name__ == "__main__":
    main()