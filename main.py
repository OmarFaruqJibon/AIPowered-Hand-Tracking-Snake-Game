import pygame
import cv2
from game import SnakeGame
from hand_tracker import HandTracker, CAM_W, CAM_H

# ---------------- Config ----------------
CELL_SIZE = 20
GRID_W = 28
GRID_H = 21
FPS = 3
PREVIEW_W, PREVIEW_H = 160, 120

BLACK = (0,0,0)
WHITE = (255,255,255)
RED = (200,0,0)
GREEN = (0,200,0)
GRAY = (50,50,50)
BLUE = (0,0,200)
YELLOW = (255,255,0)

def main():
    pygame.init()
    screen_w = GRID_W * CELL_SIZE
    screen_h = GRID_H * CELL_SIZE

    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("AI-Powered Snake - Hand Controlled")

    font = pygame.font.SysFont(None, 28)
    clock = pygame.time.Clock()

    tracker = HandTracker()
    game = SnakeGame(GRID_W, GRID_H, CELL_SIZE)

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                tracker.release()
                pygame.quit()
                return
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r and game.game_over:
                    game.reset()

        # ----- Camera + hand -----
        frame, hands, _ = tracker.read_frame()
        if frame is None:
            break

        requested_dir, index_pos = tracker.get_direction(hands)

        if requested_dir:
            game.dir = game.clamp_dir(requested_dir)

        # ----- Game step -----
        if not game.game_over:
            game.step()

        # ----- Draw -----
        screen.fill(BLACK)

        # Grid
        for x in range(GRID_W):
            pygame.draw.line(screen, GRAY, (x*CELL_SIZE, 0), (x*CELL_SIZE, screen_h))
        for y in range(GRID_H):
            pygame.draw.line(screen, GRAY, (0, y*CELL_SIZE), (screen_w, y*CELL_SIZE))

        # Food
        if game.food:
            fx, fy = game.food
            pygame.draw.rect(screen, RED, (fx*CELL_SIZE, fy*CELL_SIZE, CELL_SIZE, CELL_SIZE))

        # Snake
        for i, (sx, sy) in enumerate(game.snake):
            color = BLUE if i == 0 else GREEN
            pygame.draw.rect(screen, color, (sx*CELL_SIZE, sy*CELL_SIZE, CELL_SIZE, CELL_SIZE))

        # Score
        screen.blit(font.render(f"Score: {game.score}", True, WHITE), (10, 10))

        # Game over
        if game.game_over:
            txt = font.render("GAME OVER - Press R to Restart", True, RED)
            screen.blit(txt, (screen_w//2 - txt.get_width()//2, screen_h//2))

        # ---- Camera preview ----
        preview = cv2.resize(frame, (PREVIEW_W, PREVIEW_H))
        preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
        surf = pygame.image.frombuffer(preview.tobytes(), (PREVIEW_W, PREVIEW_H), "RGB")

        px = screen_w - PREVIEW_W - 10
        py = 10
        screen.blit(surf, (px, py))

        # zones
        third_w = PREVIEW_W // 3
        third_h = PREVIEW_H // 3

        pygame.draw.line(screen, GRAY, (px + third_w, py), (px + third_w, py + PREVIEW_H))
        pygame.draw.line(screen, GRAY, (px + 2*third_w, py), (px + 2*third_w, py + PREVIEW_H))
        pygame.draw.line(screen, GRAY, (px, py + third_h), (px + PREVIEW_W, py + third_h))
        pygame.draw.line(screen, GRAY, (px, py + 2*third_h), (px + PREVIEW_W, py + 2*third_h))

        # yellow dot
        if index_pos:
            ix, iy = index_pos
            dx = int((ix / CAM_W) * PREVIEW_W)
            dy = int((iy / CAM_H) * PREVIEW_H)
            pygame.draw.circle(screen, YELLOW, (px + dx, py + dy), 4)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
