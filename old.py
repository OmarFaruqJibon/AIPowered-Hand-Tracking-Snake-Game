# ai_snake_hand_control.py
import cv2
import numpy as np
import random
import pygame
from cvzone.HandTrackingModule import HandDetector
import time




# ---------------- Config ----------------
CAM_W, CAM_H = 640, 480        # camera capture size
PREVIEW_W, PREVIEW_H = 160, 120  # camera preview in-game
CELL_SIZE = 20                # size of each grid cell (pixels)
GRID_W = 28                   # number of columns (adjust to fit window)
GRID_H = 21                   # number of rows
FPS = 2                    # snake speed (frames per second)
INPUT_COOLDOWN_FRAMES = 5     # debounce frames between direction changes

# Colors
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (200,0,0)
GREEN = (0,200,0)
GRAY = (50,50,50)
BLUE = (0,0,200)

# ---------------- Helpers ----------------
def clamp_dir(prev, new):
    """Prevent the snake from reversing directly."""
    if prev == (1,0) and new == (-1,0): return prev
    if prev == (-1,0) and new == (1,0): return prev
    if prev == (0,1) and new == (0,-1): return prev
    if prev == (0,-1) and new == (0,1): return prev
    return new

def index_to_dir(ix, iy, w, h):
    """Map index finger position to one of four directions by dividing frame into zones.
       - Left third -> left
       - Right third -> right
       - Top third -> up
       - Bottom third -> down
       If inside center zone returns None (no change).
    """
    left_th = w // 3
    right_th = 2 * w // 3
    top_th = h // 3
    bottom_th = 2 * h // 3

    if ix < left_th:
        return (-1, 0)  # left
    if ix > right_th:
        return (1, 0)   # right
    if iy < top_th:
        return (0, -1)  # up
    if iy > bottom_th:
        return (0, 1)   # down
    return None

# ---------------- Game class ----------------
class SnakeGame:
    def __init__(self, cols, rows, cell_size):
        self.cols = cols
        self.rows = rows
        self.cell = cell_size
        self.reset()

    def reset(self):
        midx = self.cols // 2
        midy = self.rows // 2
        self.snake = [(midx, midy), (midx-1, midy), (midx-2, midy)]  # head first
        self.dir = (1, 0)  # start moving right
        self.spawn_food()
        self.score = 0
        self.game_over = False

    def spawn_food(self):
        free = [(x,y) for x in range(self.cols) for y in range(self.rows) if (x,y) not in self.snake]
        self.food = random.choice(free) if free else None

    def step(self):
        if self.game_over:
            return
        head = self.snake[0]
        new_head = (head[0] + self.dir[0], head[1] + self.dir[1])

        # Check collisions
        if (new_head[0] < 0 or new_head[0] >= self.cols or
            new_head[1] < 0 or new_head[1] >= self.rows or
            new_head in self.snake):
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        if self.food and new_head == self.food:
            self.score += 1
            self.spawn_food()
        else:
            self.snake.pop()

# ---------------- Main ----------------
def main():
    pygame.init()
    screen_w = GRID_W * CELL_SIZE
    screen_h = GRID_H * CELL_SIZE
    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("AI-Powered Snake - Hand Controlled")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)

    # Camera & hand detector
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
    detector = HandDetector(maxHands=1, detectionCon=0.6)

    game = SnakeGame(GRID_W, GRID_H, CELL_SIZE)

    input_cooldown = 0
    last_index_pos = None
    show_preview = True

    while True:
        # Pygame events
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                return
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r and game.game_over:
                    game.reset()
                if ev.key == pygame.K_p:
                    game.game_over = not game.game_over

        # Capture frame and detect hand
        success, frame = cap.read()
        if not success:
            print("Can't access camera")
            break
        frame = cv2.flip(frame, 1)  # mirror
        hands, img = detector.findHands(frame, flipType=False, draw=False)  # returns processed image and hands list

        requested_dir = None
        if hands:
            hand = hands[0]
            lmList = hand["lmList"]  # 21 landmarks
            # index finger tip is landmark 8
            ix, iy = int(lmList[8][0]), int(lmList[8][1])
            requested_dir = index_to_dir(ix, iy, CAM_W, CAM_H)
            last_index_pos = (ix, iy)
        else:
            requested_dir = None

        # Apply debounce for direction changes
        if requested_dir is not None and input_cooldown == 0 and not game.game_over:
            new_dir = clamp_dir(game.dir, requested_dir)
            if new_dir != game.dir:
                game.dir = new_dir
                input_cooldown = INPUT_COOLDOWN_FRAMES

        if input_cooldown > 0:
            input_cooldown -= 1

        # Advance game
        if not game.game_over:
            game.step()

        # Draw
        screen.fill(BLACK)

        # grid (optional)
        for x in range(GRID_W):
            pygame.draw.line(screen, GRAY, (x*CELL_SIZE,0),(x*CELL_SIZE,screen_h))
        for y in range(GRID_H):
            pygame.draw.line(screen, GRAY, (0,y*CELL_SIZE),(screen_w,y*CELL_SIZE))

        # Draw food
        if game.food:
            fx, fy = game.food
            pygame.draw.rect(screen, RED, (fx*CELL_SIZE, fy*CELL_SIZE, CELL_SIZE, CELL_SIZE))

        # Draw snake
        for i, (sx, sy) in enumerate(game.snake):
            rect = (sx*CELL_SIZE, sy*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if i == 0:
                pygame.draw.rect(screen, BLUE, rect)
            else:
                pygame.draw.rect(screen, GREEN, rect)

        # Score & status
        score_surf = font.render(f"Score: {game.score}", True, WHITE)
        screen.blit(score_surf, (10,10))

        if game.game_over:
            go_surf = font.render("GAME OVER - Press R to Restart", True, RED)
            screen.blit(go_surf, (screen_w//2 - go_surf.get_width()//2, screen_h//2 - 10))

        # Camera preview
        if show_preview:
            # create small preview
            preview = cv2.resize(frame, (PREVIEW_W, PREVIEW_H))
            preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
            surf = pygame.image.frombuffer(preview.tobytes(), (PREVIEW_W, PREVIEW_H), "RGB")
            screen.blit(surf, (screen_w - PREVIEW_W - 10, 10))

            # draw zones overlay on preview to help calibration
            pygame.draw.rect(screen, WHITE, (screen_w - PREVIEW_W - 10, 10, PREVIEW_W, PREVIEW_H), 1)
            # optionally draw dividing lines (visual aid)
            third_w = PREVIEW_W // 3
            third_h = PREVIEW_H // 3
            base_x = screen_w - PREVIEW_W - 10
            base_y = 10
            pygame.draw.line(screen, GRAY, (base_x + third_w, base_y), (base_x + third_w, base_y + PREVIEW_H))
            pygame.draw.line(screen, GRAY, (base_x + 2*third_w, base_y), (base_x + 2*third_w, base_y + PREVIEW_H))
            pygame.draw.line(screen, GRAY, (base_x, base_y + third_h), (base_x + PREVIEW_W, base_y + third_h))
            pygame.draw.line(screen, GRAY, (base_x, base_y + 2*third_h), (base_x + PREVIEW_W, base_y + 2*third_h))

            # show index finger dot on preview
            if last_index_pos:
                # map original cam coords to preview coords (because frame mirrored, but we used mirrored frame coords)
                ix, iy = last_index_pos
                px = int((ix / CAM_W) * PREVIEW_W)
                py = int((iy / CAM_H) * PREVIEW_H)
                pygame.draw.circle(screen, (255,255,0), (base_x + px, base_y + py), 4)

        pygame.display.flip()
        clock.tick(FPS)

    cap.release()
    pygame.quit()

if __name__ == "__main__":
    main()
