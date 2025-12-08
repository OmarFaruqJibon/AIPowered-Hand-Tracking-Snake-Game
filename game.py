# game.py
import random

class SnakeGame:
    def __init__(self, cols, rows, cell_size):
        self.cols = cols
        self.rows = rows
        self.cell = cell_size
        self.reset()

    def reset(self):
        midx = self.cols // 2
        midy = self.rows // 2
        self.snake = [(midx, midy), (midx - 1, midy), (midx - 2, midy)]
        self.dir = (1, 0)
        self.spawn_food()
        self.score = 0
        self.game_over = False
        self.paused = False

    def spawn_food(self):
        free = [(x, y) for x in range(self.cols) for y in range(self.rows)
                if (x, y) not in self.snake]
        self.food = random.choice(free) if free else None

    def clamp_dir(self, new):
        px, py = self.dir
        nx, ny = new
        # prevent reversing
        if (px == 1 and nx == -1) or (px == -1 and nx == 1) or (py == 1 and ny == -1) or (py == -1 and ny == 1):
            return self.dir
        return new

    def step(self):
        if self.game_over or self.paused:
            return

        head = self.snake[0]
        dx, dy = self.dir
        new_head = (head[0] + dx, head[1] + dy)

        # WRAP (Option A)
        new_x, new_y = new_head
        if new_x < 0:
            new_x = self.cols - 1
        elif new_x >= self.cols:
            new_x = 0
        if new_y < 0:
            new_y = self.rows - 1
        elif new_y >= self.rows:
            new_y = 0
        new_head = (new_x, new_y)

        # collision with self
        if new_head in self.snake:
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        if self.food and new_head == self.food:
            self.score += 1
            self.spawn_food()
        else:
            self.snake.pop()
