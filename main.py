import pygame
import sys
import math
import random
import asyncio  # Import asyncio for the asynchronous main loop

# ---------------------
# INITIALIZATION & CONSTANTS
# ---------------------
pygame.init()
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# Colors
WHITE      = (255, 255, 255)
BLACK      = (0, 0, 0)
GREY       = (100, 100, 100)
LIGHT_GREY = (180, 180, 180)
GREEN      = (0, 255, 0)
RED        = (255, 0, 0)
BLUE       = (50, 100, 255)
YELLOW     = (255, 255, 0)
ORANGE     = (255, 165, 0)
CYAN       = (0, 255, 255)
MAGENTA    = (255, 0, 255)
BROWN      = (139, 69, 19)

# Game States
STATE_MENU     = "MENU"
STATE_GAME     = "GAME"
STATE_PAUSE    = "PAUSE"
STATE_GAMEOVER = "GAMEOVER"
STATE_VICTORY  = "VICTORY"

# Difficulty modifiers
DIFFICULTY_SETTINGS = {
    "Easy": 0.8,
    "Normal": 1.0,
    "Hard": 1.2
}

# Global screen and clock
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tower Defense Game")
clock = pygame.time.Clock()

# Show system cursor
pygame.mouse.set_visible(True)

# ---------------------
# UTILITY CLASSES
# ---------------------
class Button:
    def __init__(self, rect, text, callback, font_size=20, color=GREY, text_color=WHITE):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.color = color
        self.text_color = text_color
        self.font = pygame.font.SysFont("Arial", font_size)
    
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.callback()

class TowerOption:
    def __init__(self, tower_type, cost, rect):
        self.tower_type = tower_type
        self.cost = cost
        self.rect = pygame.Rect(rect)
    
    def draw(self, surface, is_selected):
        bg_color = LIGHT_GREY if is_selected else GREY
        pygame.draw.rect(surface, bg_color, self.rect)
        font = pygame.font.SysFont("Arial", 16)
        text = f"{self.tower_type}\n${self.cost}"
        lines = text.splitlines()
        for i, line in enumerate(lines):
            txt_surf = font.render(line, True, BLACK)
            txt_rect = txt_surf.get_rect(center=(self.rect.centerx, self.rect.centery - 10 + i*15))
            surface.blit(txt_surf, txt_rect)

# ---------------------
# MAP CLASS
# ---------------------
class Map:
    def __init__(self, map_id):
        self.map_id = map_id
        self.path = self.generate_path(map_id)
        self.background_color = (34, 139, 34)  # Forest green
    
    def generate_path(self, map_id):
        if map_id == 1:
            return [(0, SCREEN_HEIGHT//2), (SCREEN_WIDTH - 200, SCREEN_HEIGHT//2)]
        elif map_id == 2:
            return [(0, 100), (250, 100), (250, 300), (500, 300), (500, 150), (750, 150), (750, 400), (SCREEN_WIDTH - 200, 400)]
        elif map_id == 3:
            return [(0, SCREEN_HEIGHT-100), (200, SCREEN_HEIGHT-100), (200, 300), (400, 300), (400, 500), (600, 500), (600, 150), (SCREEN_WIDTH - 200, 150)]
        elif map_id == 4:
            return [(0, 50), (150, 50), (150, 250), (350, 250), (350, 450), (550, 450), (550, 250), (SCREEN_WIDTH - 200, 250)]
        elif map_id == 5:
            return [(0, SCREEN_HEIGHT//4), (SCREEN_WIDTH//3, SCREEN_HEIGHT//4), (SCREEN_WIDTH//3, SCREEN_HEIGHT//2), 
                    (2*SCREEN_WIDTH//3, SCREEN_HEIGHT//2), (2*SCREEN_WIDTH//3, 3*SCREEN_HEIGHT//4), (SCREEN_WIDTH - 200, 3*SCREEN_HEIGHT//4)]
        else:
            return [(0, SCREEN_HEIGHT//2), (SCREEN_WIDTH - 200, SCREEN_HEIGHT//2)]
    
    def draw(self, surface):
        surface.fill(self.background_color)
        if len(self.path) > 1:
            pygame.draw.lines(surface, LIGHT_GREY, False, self.path, 40)

# ---------------------
# ENEMY CLASS
# ---------------------
class Enemy:
    def __init__(self, enemy_type, path, difficulty_modifier):
        self.path = path
        self.enemy_type = enemy_type
        self.difficulty_modifier = difficulty_modifier
        self.pos = list(path[0])
        self.current_wp = 1
        self.radius = 10
        self.kill_counted = False
        if enemy_type == "Normal":
            self.max_health = 100 * difficulty_modifier
            self.speed = 1.0
            self.reward = 10
        elif enemy_type == "Fast":
            self.max_health = 70 * difficulty_modifier
            self.speed = 1.5
            self.reward = 12
        elif enemy_type == "Tank":
            self.max_health = 200 * difficulty_modifier
            self.speed = 0.5
            self.reward = 20
        elif enemy_type == "Armored":
            self.max_health = 150 * difficulty_modifier
            self.speed = 0.8
            self.reward = 15
        elif enemy_type == "Boss":
            self.max_health = 500 * difficulty_modifier
            self.speed = 0.7
            self.reward = 50
        self.health = self.max_health

    def get_progress(self):
        if self.current_wp >= len(self.path):
            return len(self.path)
        prev_point = self.path[self.current_wp - 1]
        next_point = self.path[self.current_wp]
        segment_length = math.hypot(next_point[0]-prev_point[0], next_point[1]-prev_point[1])
        fraction = 0 if segment_length == 0 else math.hypot(self.pos[0]-prev_point[0], self.pos[1]-prev_point[1]) / segment_length
        return self.current_wp - 1 + fraction

    def update(self):
        if self.current_wp < len(self.path):
            target = self.path[self.current_wp]
            dx = target[0] - self.pos[0]
            dy = target[1] - self.pos[1]
            distance = math.hypot(dx, dy)
            if distance == 0:
                self.current_wp += 1
            else:
                dx, dy = dx / distance, dy / distance
                self.pos[0] += dx * self.speed
                self.pos[1] += dy * self.speed
                if math.hypot(target[0]-self.pos[0], target[1]-self.pos[1]) < self.speed:
                    self.current_wp += 1

    def draw(self, surface):
        if self.enemy_type == "Normal":
            pygame.draw.circle(surface, RED, (int(self.pos[0]), int(self.pos[1])), 12)
        elif self.enemy_type == "Fast":
            pygame.draw.ellipse(surface, MAGENTA, (self.pos[0]-10, self.pos[1]-7, 20, 14))
        elif self.enemy_type == "Tank":
            pygame.draw.rect(surface, (80,80,80), (self.pos[0]-12, self.pos[1]-12, 24, 24))
        elif self.enemy_type == "Armored":
            points = [(self.pos[0], self.pos[1]-14), (self.pos[0]-10, self.pos[1]), (self.pos[0], self.pos[1]+14), (self.pos[0]+10, self.pos[1])]
            pygame.draw.polygon(surface, GREEN, points)
        elif self.enemy_type == "Boss":
            pygame.draw.circle(surface, BLACK, (int(self.pos[0]), int(self.pos[1])), 20)
            pygame.draw.circle(surface, RED, (int(self.pos[0]), int(self.pos[1])), 15)
        bar_width = 30
        bar_height = 5
        health_ratio = self.health / self.max_health
        pygame.draw.rect(surface, BLACK, (self.pos[0]-bar_width/2, self.pos[1]-25, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (self.pos[0]-bar_width/2, self.pos[1]-25, bar_width * health_ratio, bar_height))

    def is_dead(self):
        return self.health <= 0

    def reached_end(self):
        return self.current_wp >= len(self.path)

# ---------------------
# Helper: Draw tower shape with alpha (for ghost preview)
# ---------------------
def draw_tower_shape(surface, tower_type, pos, color_with_alpha):
    x, y = pos
    color, alpha = color_with_alpha[:3], color_with_alpha[3]
    if tower_type == "Basic":
        pygame.draw.circle(surface, color + (alpha,), (x, y), 15)
    elif tower_type == "Sniper":
        s = pygame.Surface((20, 20), pygame.SRCALPHA)
        s.fill(color + (alpha,))
        surface.blit(s, (x-10, y-10))
    elif tower_type == "Splash":
        points = [(x, y-15), (x-15, y+15), (x+15, y+15)]
        pygame.draw.polygon(surface, color + (alpha,), points)
    elif tower_type == "Slow":
        points = [(x-10, y), (x-5, y-10), (x+5, y-10), (x+10, y), (x+5, y+10), (x-5, y+10)]
        pygame.draw.polygon(surface, color + (alpha,), points)
    elif tower_type == "Rapid":
        points = [
            (x, y-15),
            (x+4, y-4),
            (x+15, y-4),
            (x+7, y+2),
            (x+10, y+15),
            (x, y+7),
            (x-10, y+15),
            (x-7, y+2),
            (x-15, y-4),
            (x-4, y-4)
        ]
        pygame.draw.polygon(surface, color + (alpha,), points)

# ---------------------
# TOWER CLASS
# ---------------------
class Tower:
    def __init__(self, pos, tower_type):
        self.pos = pos
        self.tower_type = tower_type
        self.level = 1
        self.priority = "first"  # Options: "first", "last", "strong", "weak"
        self.last_shot_time = 0
        self.kills = 0
        self.game = None  # This will be set by the game when the tower is created.
        if tower_type == "Basic":
            self.range = 100
            self.damage = 25
            self.fire_rate = 1000  # ms
            self.cost = 50
        elif tower_type == "Sniper":
            self.range = int(150 * 1.2)
            self.damage = 50
            self.fire_rate = int(2000 * 1.2)
            self.cost = 100
        elif tower_type == "Splash":
            self.range = 80
            self.damage = 20
            self.fire_rate = 1500
            self.cost = 75
        elif tower_type == "Slow":
            self.range = 90
            self.damage = 15
            self.fire_rate = 1500
            self.cost = 80
        elif tower_type == "Rapid":
            self.range = 70
            self.damage = 10
            self.fire_rate = 500
            self.cost = 60

    def can_shoot(self, current_time):
        return current_time - self.last_shot_time >= self.fire_rate

    def shoot(self, target, current_time):
        self.last_shot_time = current_time
        # FIX: Use self.game instead of self.owner.game
        return Projectile(self.pos, target, self.damage, self, self.game)

    def upgrade(self):
        self.level += 1
        self.damage = int(self.damage * 1.2)
        self.range = int(self.range * 1.1)
        self.fire_rate = max(int(self.fire_rate * 0.9), 200)

    def draw(self, surface, highlight=False):
        x, y = self.pos
        if self.tower_type == "Basic":
            pygame.draw.circle(surface, BLUE, (x, y), 15)
        elif self.tower_type == "Sniper":
            rect = pygame.Rect(x-10, y-10, 20, 20)
            pygame.draw.rect(surface, YELLOW, rect)
        elif self.tower_type == "Splash":
            points = [(x, y-15), (x-15, y+15), (x+15, y+15)]
            pygame.draw.polygon(surface, ORANGE, points)
        elif self.tower_type == "Slow":
            points = [(x-10, y), (x-5, y-10), (x+5, y-10), (x+10, y), (x+5, y+10), (x-5, y+10)]
            pygame.draw.polygon(surface, CYAN, points)
        elif self.tower_type == "Rapid":
            points = [
                (x, y-15),
                (x+4, y-4),
                (x+15, y-4),
                (x+7, y+2),
                (x+10, y+15),
                (x, y+7),
                (x-10, y+15),
                (x-7, y+2),
                (x-15, y-4),
                (x-4, y-4)
            ]
            pygame.draw.polygon(surface, MAGENTA, points)
        if highlight:
            pygame.draw.circle(surface, WHITE, self.pos, 20, 3)
            pygame.draw.circle(surface, WHITE, self.pos, self.range, 1)
        # Draw tower info: level, DPS, kills
        font = pygame.font.SysFont("Arial", 12)
        level_text = font.render(f"Lv {self.level}", True, WHITE)
        dps = int(self.damage * 1000 / self.fire_rate)
        dps_text = font.render(f"DPS: {dps}", True, WHITE)
        kills_text = font.render(f"Kills: {self.kills}", True, WHITE)
        surface.blit(level_text, (x-15, y-35))
        surface.blit(dps_text, (x-15, y+20))
        surface.blit(kills_text, (x-15, y+35))

# ---------------------
# PROJECTILE CLASS
# ---------------------
class Projectile:
    def __init__(self, pos, target, damage, owner, game):
        self.pos = list(pos)
        self.target = target
        self.damage = damage
        self.owner = owner
        self.speed = 5
        self.radius = 5
        self.active = True
        self.game = game

        if self.owner.tower_type == "Splash":
            self.speed *= 0.8
            self.radius = int(self.radius * 1.2)
        if self.owner.tower_type == "Sniper":
            self.speed *= 2

    def update(self):
        if not self.active or self.target.is_dead():
            self.active = False
            return
        dx = self.target.pos[0] - self.pos[0]
        dy = self.target.pos[1] - self.pos[1]
        distance = math.hypot(dx, dy)
        if distance < self.speed:
            self.target.health -= self.damage
            if self.target.health <= 0 and not self.target.kill_counted:
                self.target.kill_counted = True
                self.owner.kills += 1
            if self.owner.tower_type == "Splash":
                for enemy in self.owner.game.enemies:
                    if math.hypot(enemy.pos[0] - self.pos[0], enemy.pos[1] - self.pos[1]) <= self.radius * 2:
                        enemy.health -= self.damage
                        if enemy.health <= 0 and not enemy.kill_counted:
                            enemy.kill_counted = True
                            self.owner.kills += 1
            self.active = False
        else:
            dx, dy = dx / distance, dy / distance
            self.pos[0] += dx * self.speed
            self.pos[1] += dy * self.speed

    def draw(self, surface):
        if self.active:
            pygame.draw.circle(surface, BLACK, (int(self.pos[0]), int(self.pos[1])), self.radius)

# ---------------------
# NUKE ANIMATION CLASS
# ---------------------
class NukeAnimation:
    def __init__(self, pos):
        self.pos = pos
        self.radius = 0
        self.max_radius = 200
        self.alpha = 255
        self.finished = False

    def update(self, dt):
        self.radius += dt * 0.5
        self.alpha = max(255 - int((self.radius / self.max_radius) * 255), 0)
        if self.radius >= self.max_radius:
            self.finished = True

    def draw(self, surface):
        s = pygame.Surface((self.max_radius*2, self.max_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 0, self.alpha), (self.max_radius, self.max_radius), int(self.radius))
        surface.blit(s, (self.pos[0]-self.max_radius, self.pos[1]-self.max_radius))

# ---------------------
# LEVEL CLASS
# ---------------------
class Level:
    def __init__(self, level_number, game):
        self.level_number = level_number
        self.game = game
        self.spawn_timer = 0
        self.spawn_interval = max(1000 - level_number * 50, 300)
        self.enemies_to_spawn = 5 + level_number * 2
        self.enemies_spawned = 0
        self.finished_spawning = False
        self.enemy_types = ["Normal", "Fast", "Tank", "Armored"]
        if level_number % 5 == 0:
            self.enemy_types.append("Boss")
        else:
            self.enemy_types.append("Normal")
    
    def update(self, dt):
        if not self.finished_spawning:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval and self.enemies_spawned < self.enemies_to_spawn:
                self.spawn_timer = 0
                enemy_type = random.choice(self.enemy_types)
                enemy = Enemy(enemy_type, self.game.game_map.path, self.game.difficulty_modifier)
                self.game.enemies.append(enemy)
                self.enemies_spawned += 1
            if self.enemies_spawned >= self.enemies_to_spawn:
                self.finished_spawning = True

# ---------------------
# GAME CLASS
# ---------------------
class Game:
    def __init__(self):
        self.state = STATE_MENU
        self.difficulty = "Normal"
        self.difficulty_modifier = DIFFICULTY_SETTINGS[self.difficulty]
        self.selected_map_id = 1
        self.game_map = Map(self.selected_map_id)
        self.level_number = 1
        self.level = Level(self.level_number, self)
        self.towers = []
        self.enemies = []
        self.projectiles = []
        self.nuke_animations = []
        self.money = 300
        self.lives = 20
        self.last_update = pygame.time.get_ticks()
        self.selected_tower_type = "Basic"  # None means no purchase selected
        self.selected_tower = None          # For tower menu interactions
        self.speed = 1  # 1x speed by default; 2 means double update iterations
        self.create_menu_buttons()
        self.create_hud_buttons()
        self.create_purchase_bar()
        self.tower_menu_buttons = {}

    def create_menu_buttons(self):
        self.menu_buttons = []
        start_button = Button((SCREEN_WIDTH//2 - 100, 200, 200, 50), "Start Game", self.start_game, font_size=28)
        difficulty_button = Button((SCREEN_WIDTH//2 - 100, 270, 200, 50), "Difficulty", self.change_difficulty, font_size=28)
        map_button = Button((SCREEN_WIDTH//2 - 100, 340, 200, 50), "Select Map", self.select_map, font_size=28)
        quit_button = Button((SCREEN_WIDTH//2 - 100, 410, 200, 50), "Quit", self.quit_game, font_size=28)
        self.menu_buttons.extend([start_button, difficulty_button, map_button, quit_button])
    
    def create_hud_buttons(self):
        self.hud_buttons = []
        self.play_pause_button = Button((10, 10, 80, 30), "Pause", self.toggle_pause, font_size=18)
        self.speed1_button = Button((100, 10, 50, 30), "1x", lambda: self.set_speed(1), font_size=18)
        self.speed2_button = Button((160, 10, 50, 30), "2x", lambda: self.set_speed(2), font_size=18)
        self.nuke_button = Button((220, 10, 80, 30), "NUKE", self.activate_nuke, font_size=18, color=ORANGE)
        self.exit_button = Button((SCREEN_WIDTH - 110, 10, 100, 30), "Exit", self.return_to_menu, font_size=18)
        self.hud_buttons.extend([self.play_pause_button, self.speed1_button, self.speed2_button, self.nuke_button, self.exit_button])

    def create_purchase_bar(self):
        self.purchase_options = []
        tower_types = [("Basic", 50), ("Sniper", 100), ("Splash", 75), ("Slow", 80), ("Rapid", 60)]
        num = len(tower_types)
        bar_height = 80
        option_width = 100
        spacing = 20
        total_width = num * option_width + (num - 1) * spacing
        start_x = (SCREEN_WIDTH - total_width) // 2
        y = SCREEN_HEIGHT - bar_height + 10
        for i, (t_type, cost) in enumerate(tower_types):
            rect = (start_x + i*(option_width+spacing), SCREEN_HEIGHT - bar_height + 5, option_width, bar_height - 10)
            self.purchase_options.append(TowerOption(t_type, cost, rect))

    def start_game(self):
        self.reset_game()
        self.state = STATE_GAME

    def change_difficulty(self):
        difficulties = list(DIFFICULTY_SETTINGS.keys())
        idx = difficulties.index(self.difficulty)
        self.difficulty = difficulties[(idx + 1) % len(difficulties)]
        self.difficulty_modifier = DIFFICULTY_SETTINGS[self.difficulty]

    def select_map(self):
        self.selected_map_id = self.selected_map_id % 5 + 1
        self.game_map = Map(self.selected_map_id)

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def reset_game(self):
        self.level_number = 1
        self.level = Level(self.level_number, self)
        self.towers = []
        self.enemies = []
        self.projectiles = []
        self.nuke_animations = []
        self.money = 300
        self.lives = 20
        self.selected_tower = None

    def toggle_pause(self):
        if self.state == STATE_GAME:
            self.state = STATE_PAUSE
            self.play_pause_button.text = "Play"
        elif self.state == STATE_PAUSE:
            self.state = STATE_GAME
            self.play_pause_button.text = "Pause"

    def set_speed(self, spd):
        self.speed = spd

    def activate_nuke(self):
        for enemy in self.enemies:
            enemy.health = 0
        self.nuke_animations.append(NukeAnimation((SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))

    def choose_target_for_tower(self, tower):
        in_range = [enemy for enemy in self.enemies if math.hypot(tower.pos[0]-enemy.pos[0], tower.pos[1]-enemy.pos[1]) <= tower.range]
        if not in_range:
            return None
        if tower.priority == "first":
            return max(in_range, key=lambda e: e.get_progress())
        elif tower.priority == "last":
            return min(in_range, key=lambda e: e.get_progress())
        elif tower.priority == "strong":
            return max(in_range, key=lambda e: e.health)
        elif tower.priority == "weak":
            return min(in_range, key=lambda e: e.health)
        else:
            return in_range[0]

    def update(self, dt):
        if self.state == STATE_GAME:
            for _ in range(self.speed):
                self.level.update(dt)
                for enemy in self.enemies:
                    enemy.update()
                current_time = pygame.time.get_ticks()
                for tower in self.towers:
                    if tower.can_shoot(current_time):
                        target = self.choose_target_for_tower(tower)
                        if target:
                            proj = tower.shoot(target, current_time)
                            self.projectiles.append(proj)
                for proj in self.projectiles:
                    proj.update()
            for enemy in self.enemies[:]:
                if enemy.is_dead():
                    self.money += enemy.reward
                    self.enemies.remove(enemy)
                elif enemy.reached_end():
                    self.lives -= 1
                    self.enemies.remove(enemy)
            self.projectiles = [p for p in self.projectiles if p.active]
            for nuke in self.nuke_animations:
                nuke.update(dt)
            self.nuke_animations = [n for n in self.nuke_animations if not n.finished]
            if self.level.finished_spawning and not self.enemies:
                self.level_number += 1
                if self.level_number > 15:
                    self.state = STATE_VICTORY
                else:
                    self.level = Level(self.level_number, self)
            if self.lives <= 0:
                self.state = STATE_GAMEOVER

    def draw(self, surface):
        if self.state == STATE_MENU:
            surface.fill(BLACK)
            font = pygame.font.SysFont("Arial", 36)
            title_surf = font.render("Tower Defense Game", True, WHITE)
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH//2, 100))
            surface.blit(title_surf, title_rect)
            for btn in self.menu_buttons:
                btn.draw(surface)
            info_font = pygame.font.SysFont("Arial", 24)
            diff_surf = info_font.render(f"Difficulty: {self.difficulty}", True, WHITE)
            map_surf = info_font.render(f"Map: {self.selected_map_id}", True, WHITE)
            surface.blit(diff_surf, (SCREEN_WIDTH//2 - 100, 480))
            surface.blit(map_surf, (SCREEN_WIDTH//2 - 100, 510))
            map_preview = Map(self.selected_map_id)
            preview_surface = pygame.Surface((200, 100))
            preview_surface.fill((34, 139, 34))
            scaled_path = [(int(x * 200 / SCREEN_WIDTH), int(y * 100 / SCREEN_HEIGHT)) for x, y in map_preview.path]
            if len(scaled_path) > 1:
                pygame.draw.lines(preview_surface, LIGHT_GREY, False, scaled_path, 4)
            preview_rect = preview_surface.get_rect(center=(SCREEN_WIDTH//2, 600))
            surface.blit(preview_surface, preview_rect)
        elif self.state in (STATE_GAME, STATE_PAUSE):
            self.game_map.draw(surface)
            for tower in self.towers:
                highlight = (tower == self.selected_tower)
                tower.draw(surface, highlight)
            for enemy in self.enemies:
                enemy.draw(surface)
            for proj in self.projectiles:
                proj.draw(surface)
            for nuke in self.nuke_animations:
                nuke.draw(surface)
            hud_font = pygame.font.SysFont("Arial", 20)
            hud_text = f"Money: {self.money}   Lives: {self.lives}   Level: {self.level_number}"
            hud_surf = hud_font.render(hud_text, True, BLACK)
            surface.blit(hud_surf, (10, 50))
            for btn in self.hud_buttons:
                btn.draw(surface)
            for option in self.purchase_options:
                is_selected = (option.tower_type == self.selected_tower_type)
                option.draw(surface, is_selected)
            purchase_bar_rect = pygame.Rect(0, SCREEN_HEIGHT - 80, SCREEN_WIDTH, 80)
            if self.selected_tower_type is not None and self.selected_tower is None:
                mouse_pos = pygame.mouse.get_pos()
                can_place = True
                for tower in self.towers:
                    if math.hypot(mouse_pos[0] - tower.pos[0], mouse_pos[1] - tower.pos[1]) < 30:
                        can_place = False
                        break
                preview_color = (*RED, 77) if not can_place else (*BLUE, 128)
                draw_tower_shape(surface, self.selected_tower_type, mouse_pos, preview_color)
                if can_place:
                    temp_tower = Tower(mouse_pos, self.selected_tower_type)
                    pygame.draw.circle(surface, WHITE, mouse_pos, temp_tower.range, 1)
            if self.selected_tower:
                self.draw_tower_menu(surface)
            if self.state == STATE_PAUSE:
                pause_font = pygame.font.SysFont("Arial", 48)
                pause_surf = pause_font.render("Paused", True, RED)
                pause_rect = pause_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                surface.blit(pause_surf, pause_rect)
        elif self.state == STATE_GAMEOVER:
            surface.fill(BLACK)
            font = pygame.font.SysFont("Arial", 48)
            over_surf = font.render("Game Over", True, RED)
            over_rect = over_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            surface.blit(over_surf, over_rect)
            info_font = pygame.font.SysFont("Arial", 36)
            info_surf = info_font.render("Press M for Menu", True, WHITE)
            info_rect = info_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            surface.blit(info_surf, info_rect)
        elif self.state == STATE_VICTORY:
            surface.fill(BLACK)
            font = pygame.font.SysFont("Arial", 48)
            victory_surf = font.render("Victory!", True, GREEN)
            victory_rect = victory_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            surface.blit(victory_surf, victory_rect)
            info_font = pygame.font.SysFont("Arial", 36)
            info_surf = info_font.render("Press M for Menu", True, WHITE)
            info_rect = info_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            surface.blit(info_surf, info_rect)

    def draw_tower_menu(self, surface):
        panel_rect = pygame.Rect(SCREEN_WIDTH - 200, 0, 200, SCREEN_HEIGHT)
        pygame.draw.rect(surface, LIGHT_GREY, panel_rect)
        font = pygame.font.SysFont("Arial", 24)
        title = font.render("Tower Menu", True, BLACK)
        surface.blit(title, (SCREEN_WIDTH - 180, 20))
        sell_price = int(0.75 * self.selected_tower.cost * self.selected_tower.level)
        upgrade_price = int(0.5 * self.selected_tower.cost * self.selected_tower.level)
        sell_btn_rect = pygame.Rect(SCREEN_WIDTH - 180, 60, 160, 30)
        pygame.draw.rect(surface, RED, sell_btn_rect)
        sell_text = font.render("Sell", True, WHITE)
        surface.blit(sell_text, sell_text.get_rect(center=sell_btn_rect.center))
        sell_label = pygame.font.SysFont("Arial", 16).render(f"${sell_price}", True, WHITE)
        surface.blit(sell_label, (SCREEN_WIDTH - 180, 95))
        upg_btn_rect = pygame.Rect(SCREEN_WIDTH - 180, 120, 160, 30)
        pygame.draw.rect(surface, BLUE, upg_btn_rect)
        upg_text = font.render("Upgrade", True, WHITE)
        surface.blit(upg_text, upg_text.get_rect(center=upg_btn_rect.center))
        upg_label = pygame.font.SysFont("Arial", 16).render(f"${upgrade_price}", True, WHITE)
        surface.blit(upg_label, (SCREEN_WIDTH - 180, 155))
        priorities = ["first", "last", "strong", "weak"]
        for i, prio in enumerate(priorities):
            btn_rect = pygame.Rect(SCREEN_WIDTH - 180, 200 + i*40, 160, 30)
            color = GREEN if self.selected_tower.priority == prio else GREY
            pygame.draw.rect(surface, color, btn_rect)
            prio_text = font.render(prio.capitalize(), True, BLACK)
            surface.blit(prio_text, prio_text.get_rect(center=btn_rect.center))
        self.tower_menu_buttons = {
            "sell": sell_btn_rect,
            "upgrade": upg_btn_rect,
            "first": pygame.Rect(SCREEN_WIDTH - 180, 200, 160, 30),
            "last": pygame.Rect(SCREEN_WIDTH - 180, 240, 160, 30),
            "strong": pygame.Rect(SCREEN_WIDTH - 180, 280, 160, 30),
            "weak": pygame.Rect(SCREEN_WIDTH - 180, 320, 160, 30)
        }

    def handle_event(self, event):
        if self.state == STATE_MENU:
            for btn in self.menu_buttons:
                btn.handle_event(event)
        elif self.state in (STATE_GAME, STATE_PAUSE):
            for btn in self.hud_buttons:
                btn.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if any(btn.rect.collidepoint(pos) for btn in self.hud_buttons):
                    return
                purchase_bar_rect = pygame.Rect(0, SCREEN_HEIGHT - 80, SCREEN_WIDTH, 80)
                if purchase_bar_rect.collidepoint(pos):
                    for option in self.purchase_options:
                        if option.rect.collidepoint(pos):
                            if option.tower_type == self.selected_tower_type:
                                self.selected_tower_type = None
                            else:
                                self.selected_tower_type = option.tower_type
                            return
                menu_panel_rect = pygame.Rect(SCREEN_WIDTH - 200, 0, 200, SCREEN_HEIGHT)
                if self.selected_tower and menu_panel_rect.collidepoint(pos):
                    for key, rect in self.tower_menu_buttons.items():
                        if rect.collidepoint(pos):
                            if key == "sell":
                                self.money += int(0.75 * self.selected_tower.cost * self.selected_tower.level)
                                if self.selected_tower in self.towers:
                                    self.towers.remove(self.selected_tower)
                                self.selected_tower = None
                            elif key == "upgrade":
                                upgrade_cost = int(0.5 * self.selected_tower.cost * self.selected_tower.level)
                                if self.money >= upgrade_cost:
                                    self.money -= upgrade_cost
                                    self.selected_tower.upgrade()
                            elif key in ["first", "last", "strong", "weak"]:
                                self.selected_tower.priority = key
                    return
                clicked_on_tower = False
                for tower in self.towers:
                    tx, ty = tower.pos
                    if math.hypot(pos[0]-tx, pos[1]-ty) < 20:
                        self.selected_tower = tower
                        clicked_on_tower = True
                        break
                if not clicked_on_tower:
                    self.selected_tower = None
                mouse_pos = pygame.mouse.get_pos()
                can_place = True
                for tower in self.towers:
                    if math.hypot(mouse_pos[0] - tower.pos[0], mouse_pos[1] - tower.pos[1]) < 30:
                        can_place = False
                        break
                preview_color = (*RED, 77) if not can_place else (*BLUE, 128)
                if not purchase_bar_rect.collidepoint(pos) and pos[0] < SCREEN_WIDTH - 200 and not clicked_on_tower:
                    if self.selected_tower_type is not None:
                        temp_tower = Tower(pos, self.selected_tower_type)
                        if self.money >= temp_tower.cost:
                            if preview_color[:3] != RED:
                                temp_tower.game = self  # Assign the game instance to the tower
                                self.towers.append(temp_tower)
                                self.money -= temp_tower.cost
        elif self.state == STATE_GAMEOVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                self.state = STATE_MENU
        elif self.state == STATE_VICTORY:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                self.state = STATE_MENU

    def return_to_menu(self):
        self.state = STATE_MENU

# ASYNCHRONOUS MAIN GAME LOOP (for pygbag)
# ---------------------
async def main():
    game = Game()
    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)
        if game.state == STATE_GAME:
            game.update(dt)
        game.draw(screen)
        pygame.display.flip()
        # Yield control to allow browser to process events
        await asyncio.sleep(0)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())