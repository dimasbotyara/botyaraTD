# main.py — Главный файл, запуск игры Deluxe Edition

import pygame
import sys
import math
import random
import ctypes

from settings import *
from map_data import get_path, get_map, is_buildable, get_level_info, LEVEL_DATA
from tower import Tower
from enemy import Enemy
from projectile import Projectile
from wave import get_wave
from effects import EffectsManager
from ui import (Sidebar, MainMenu, SettingsMenu, PauseMenu, GameOverScreen, LevelSelectMenu)
from sound import sound_manager


class Game:
    """Основной класс игры"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # Состояния: menu, level_select, settings, playing, paused, game_over
        self.state = "menu"
        self.hidden = False

        # Выбранный уровень (0..4)
        self.current_level = 0

        # UI Экранные компоненты
        self.main_menu = MainMenu()
        self.level_select_menu = LevelSelectMenu()
        self.settings_menu = SettingsMenu()
        self.pause_menu = PauseMenu()
        self.game_over_screen = GameOverScreen()
        self.sidebar = Sidebar()

        # Игровые объекты
        self.reset_game()

        # Окно управления
        self.hwnd = None
        try:
            self.hwnd = pygame.display.get_wm_info()["window"]
        except Exception:
            pass

    def reset_game(self):
        """Сброс состояния игры под выбранный уровень"""
        self.path = get_path(self.current_level)
        self.game_map = get_map(self.current_level)
        self.level_info = get_level_info(self.current_level)

        self.towers = []
        self.enemies = []
        self.projectiles = []
        self.effects = EffectsManager()

        self.gold = START_GOLD
        self.lives = START_LIVES
        self.wave_num = 0
        self.wave_active = False
        self.wave_queue = []
        self.spawn_timer = 0
        self.game_speed = SPEED_NORMAL
        self.kills = 0
        self.game_won = False

        # Супер-способности игрока (таймеры перезарядки в кадрах)
        self.cd_airstrike = 0
        self.max_cd_airstrike = 2700  # 45 сек
        self.cd_freeze = 0
        self.max_cd_freeze = 1800     # 30 сек
        self.cd_gold = 0
        self.max_cd_gold = 2400       # 40 сек

        self.selected_tower_type = None
        self.selected_placed_tower = None
        self.hover_cell = None

        self.sidebar.selected_tower_type = None
        self.sidebar.selected_placed_tower = None

        self.map_surface = None
        self._render_map_surface()

    def _render_map_surface(self):
        """Пре-рендер фона карты текущего уровня"""
        self.map_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        bg_col = self.level_info["bg_color"]
        bg_alt = self.level_info["bg_alt"]
        path_col = self.level_info["path_color"]
        border_col = self.level_info["border_color"]

        self.map_surface.fill(bg_col)

        game_map = self.game_map

        for row in range(len(game_map)):
            for col in range(len(game_map[0])):
                x = col * CELL_SIZE
                y = row * CELL_SIZE
                cell = game_map[row][col]

                if cell == 0:
                    # Шахматная плитка / текстура земли
                    color = bg_col if (row + col) % 2 == 0 else bg_alt
                    pygame.draw.rect(self.map_surface, color, (x, y, CELL_SIZE, CELL_SIZE))

                    # Детали ландшафта по уровню
                    random.seed(row * 100 + col + self.current_level * 50)
                    for _ in range(2):
                        gx = x + random.randint(5, CELL_SIZE - 5)
                        gy = y + random.randint(5, CELL_SIZE - 5)
                        gl = random.randint(2, 5)
                        if self.current_level == 0:
                            gc = (35, 130, 50)
                        elif self.current_level == 1:
                            gc = (180, 130, 70)
                        elif self.current_level == 2:
                            gc = (220, 240, 255)
                        elif self.current_level == 3:
                            gc = (0, 180, 220)
                        else:
                            gc = (120, 30, 20)
                        pygame.draw.line(self.map_surface, gc, (gx, gy), (gx + random.randint(-2, 2), gy - gl), 1)

                elif cell in (1, 2, 3):
                    # Дорога
                    pygame.draw.rect(self.map_surface, path_col, (x, y, CELL_SIZE, CELL_SIZE))

                    # Текстура дороги
                    random.seed(row * 100 + col + 999)
                    for _ in range(4):
                        sx = x + random.randint(2, CELL_SIZE - 3)
                        sy = y + random.randint(2, CELL_SIZE - 3)
                        sc = (
                            path_col[0] + random.randint(-15, 15),
                            path_col[1] + random.randint(-15, 15),
                            path_col[2] + random.randint(-15, 15),
                        )
                        sc = tuple(max(0, min(255, c)) for c in sc)
                        pygame.draw.circle(self.map_surface, sc, (sx, sy), random.randint(1, 2))

                    # Бордюры дороги
                    if row > 0 and game_map[row - 1][col] == 0:
                        pygame.draw.line(self.map_surface, border_col, (x, y), (x + CELL_SIZE, y), 2)
                    if row < len(game_map) - 1 and game_map[row + 1][col] == 0:
                        pygame.draw.line(self.map_surface, border_col, (x, y + CELL_SIZE - 1),
                                         (x + CELL_SIZE, y + CELL_SIZE - 1), 2)
                    if col > 0 and game_map[row][col - 1] == 0:
                        pygame.draw.line(self.map_surface, border_col, (x, y), (x, y + CELL_SIZE), 2)
                    if col < len(game_map[0]) - 1 and game_map[row][col + 1] == 0:
                        pygame.draw.line(self.map_surface, border_col, (x + CELL_SIZE - 1, y),
                                         (x + CELL_SIZE - 1, y + CELL_SIZE), 2)

        # Вход и выход
        if len(self.path) > 1:
            sx, sy = self.path[0]
            pygame.draw.polygon(self.map_surface, (50, 200, 80), [
                (sx - 5, sy - 8), (sx + 8, sy), (sx - 5, sy + 8)
            ])

            ex, ey = self.path[-1]
            pygame.draw.rect(self.map_surface, (200, 50, 50),
                             (ex - 12, ey - 12, 24, 24), border_radius=4)
            pygame.draw.rect(self.map_surface, (255, 80, 80),
                             (ex - 8, ey - 8, 16, 16), border_radius=3)
            pygame.draw.line(self.map_surface, (255, 200, 200), (ex - 5, ey - 5), (ex + 5, ey + 5), 2)
            pygame.draw.line(self.map_surface, (255, 200, 200), (ex + 5, ey - 5), (ex - 5, ey + 5), 2)

        # Анимированные стрелки дороги
        for i in range(0, len(self.path) - 1, 4):
            ax, ay = self.path[i]
            bx, by = self.path[min(i + 1, len(self.path) - 1)]
            angle = math.atan2(by - ay, bx - ax)
            arrow_len = 6
            tip_x = ax + math.cos(angle) * arrow_len
            tip_y = ay + math.sin(angle) * arrow_len
            left_x = ax + math.cos(angle + 2.5) * (arrow_len - 1)
            left_y = ay + math.sin(angle + 2.5) * (arrow_len - 1)
            right_x = ax + math.cos(angle - 2.5) * (arrow_len - 1)
            right_y = ay + math.sin(angle - 2.5) * (arrow_len - 1)
            pygame.draw.polygon(self.map_surface, (160, 130, 90), [
                (int(tip_x), int(tip_y)),
                (int(left_x), int(left_y)),
                (int(right_x), int(right_y)),
            ])

        # Сетка
        for col in range(GAME_WIDTH // CELL_SIZE + 1):
            x = col * CELL_SIZE
            pygame.draw.line(self.map_surface, (0, 0, 0, 20), (x, 0), (x, GAME_HEIGHT), 1)
        for row in range(GAME_HEIGHT // CELL_SIZE + 1):
            y = row * CELL_SIZE
            pygame.draw.line(self.map_surface, (0, 0, 0, 20), (0, y), (GAME_WIDTH, y), 1)

    def hide_window(self):
        """Скрыть/показать окно"""
        if self.hwnd is None:
            return
        try:
            SW_HIDE = 0
            SW_SHOW = 5
            if not self.hidden:
                ctypes.windll.user32.ShowWindow(self.hwnd, SW_HIDE)
                self.hidden = True
                if self.state == "playing":
                    self.state = "paused"
            else:
                ctypes.windll.user32.ShowWindow(self.hwnd, SW_SHOW)
                ctypes.windll.user32.SetForegroundWindow(self.hwnd)
                self.hidden = False
        except Exception:
            pass

    def start_wave(self):
        """Начать новую волну"""
        if self.wave_active or self.wave_num >= MAX_WAVES:
            return

        self.wave_num += 1
        self.wave_queue = get_wave(self.wave_num)
        self.wave_active = True
        self.spawn_timer = 0
        sound_manager.play("click")

        difficulty = self.settings_menu.difficulty
        if difficulty == 0:
            cut = max(3, len(self.wave_queue) * 3 // 4)
            self.wave_queue = self.wave_queue[:cut]
        elif difficulty == 2:
            extra = len(self.wave_queue) // 4
            for i in range(extra):
                self.wave_queue.append(self.wave_queue[i % len(self.wave_queue)])

    def spawn_enemy(self, enemy_type):
        """Заспавнить врага"""
        wave = self.wave_num
        difficulty = self.settings_menu.difficulty

        if difficulty == 2:
            wave = int(wave * 1.3)

        enemy = Enemy(enemy_type, self.path, wave)

        if difficulty == 0:
            enemy.hp *= 0.8
            enemy.max_hp *= 0.8
            enemy.reward = int(enemy.reward * 1.3)
        elif difficulty == 2:
            enemy.hp *= 1.2
            enemy.max_hp *= 1.2
            enemy.reward = int(enemy.reward * 0.8)

        self.enemies.append(enemy)

    def trigger_ability(self, ability_name):
        """Использовать супер-способность"""
        if ability_name == "airstrike":
            if self.cd_airstrike <= 0 and self.gold >= 100:
                self.gold -= 100
                self.cd_airstrike = self.max_cd_airstrike
                sound_manager.play("airstrike")
                self.effects.add_shake(12.0)
                # Ракетный удар по всему пути!
                for pt in self.path[::4]:
                    self.effects.add_airstrike_explosion(pt[0], pt[1])
                for enemy in self.enemies:
                    enemy.take_damage(350)
                self.effects.add_floating_text(GAME_WIDTH//2, 100, "💣 АВИАУДАР!", (255, 100, 50), 34, 80)

        elif ability_name == "freeze":
            if self.cd_freeze <= 0 and self.gold >= 50:
                self.gold -= 50
                self.cd_freeze = self.max_cd_freeze
                sound_manager.play("freeze")
                for enemy in self.enemies:
                    enemy.apply_slow(0.85, 300)  # 5 секунд 85% замедления
                    self.effects.add_freeze_effect(enemy.x, enemy.y)
                self.effects.add_floating_text(GAME_WIDTH//2, 100, "❄️ ВСЁ ЗАМОРОЖЕНО!", (100, 200, 255), 34, 80)

        elif ability_name == "gold":
            if self.cd_gold <= 0:
                self.cd_gold = self.max_cd_gold
                self.gold += 150
                sound_manager.play("gold")
                self.effects.add_gold_text(GAME_WIDTH//2, 100, 150)
                self.effects.add_floating_text(GAME_WIDTH//2, 130, "💰 ЗОЛОТАЯ ЛИХОРАДКА!", (255, 215, 0), 34, 80)

    def place_tower(self, col, row, tower_type):
        """Поставить башню"""
        cost = TOWER_STATS[tower_type]["levels"][0]["cost"]
        if self.gold < cost:
            return False
        if not is_buildable(col, row, self.current_level):
            return False

        for t in self.towers:
            if t.col == col and t.row == row:
                return False

        tower = Tower(col, row, tower_type)
        self.towers.append(tower)
        self.gold -= cost
        sound_manager.play("click")

        px = col * CELL_SIZE + CELL_SIZE // 2
        py = row * CELL_SIZE + CELL_SIZE // 2
        self.effects.add_explosion(px, py, TOWER_COLORS[tower_type], count=10, speed=2, size=3, lifetime=20)
        return True

    def sell_tower(self, tower):
        """Продать башню"""
        sell_price = tower.get_sell_price()
        self.gold += sell_price
        sound_manager.play("gold")

        px, py = tower.x, tower.y
        self.effects.add_gold_text(px, py - 20, sell_price)
        self.effects.add_explosion(px, py, (200, 200, 100), count=8, speed=2, size=3, lifetime=20)

        self.towers.remove(tower)
        self.selected_placed_tower = None
        self.sidebar.selected_placed_tower = None

    def upgrade_tower(self, tower):
        """Улучшить башню"""
        cost = tower.get_upgrade_cost()
        if cost is None or self.gold < cost:
            return False

        self.gold -= cost
        tower.upgrade()

        self.effects.add_explosion(tower.x, tower.y, TOWER_COLORS[tower.tower_type],
                                   count=15, speed=3, size=4, lifetime=25)
        self.effects.add_floating_text(tower.x, tower.y - 25, "UPGRADE!", (255, 255, 100), 24, 50)
        return True

    def update_game(self):
        """Обновление игровой логики"""
        for _ in range(self.game_speed):
            self._game_tick()

    def _game_tick(self):
        """Один тик игровой логики"""
        # Обновление перезарядок способностей
        if self.cd_airstrike > 0:
            self.cd_airstrike -= 1
        if self.cd_freeze > 0:
            self.cd_freeze -= 1
        if self.cd_gold > 0:
            self.cd_gold -= 1

        # Спавн врагов
        if self.wave_active and self.wave_queue:
            self.spawn_timer -= 1
            if self.spawn_timer <= 0:
                enemy_type, delay = self.wave_queue.pop(0)
                self.spawn_enemy(enemy_type)
                self.spawn_timer = delay

        # Конец волны
        if self.wave_active and not self.wave_queue and not self.enemies:
            self.wave_active = False
            wave_bonus = 15 + self.wave_num * 3
            difficulty = self.settings_menu.difficulty
            if difficulty == 0:
                wave_bonus = int(wave_bonus * 1.5)
            elif difficulty == 2:
                wave_bonus = int(wave_bonus * 0.7)
            self.gold += wave_bonus
            sound_manager.play("gold")
            self.effects.add_floating_text(
                GAME_WIDTH // 2, GAME_HEIGHT // 2 - 40,
                f"Волна {self.wave_num} пройдена! +{wave_bonus}g",
                (255, 215, 0), 30, 90
            )

            if self.wave_num >= MAX_WAVES:
                self.game_won = True
                self.state = "game_over"
                sound_manager.play("victory")

        # Враги
        new_enemies = []
        for enemy in self.enemies:
            enemy.update(self.enemies)

            if not enemy.alive:
                if enemy.reached_end:
                    self.lives -= 1
                    sound_manager.play("hurt")
                    self.effects.add_shake(4.0)
                    self.effects.add_floating_text(
                        enemy.x, enemy.y, "-1 HP!", (255, 50, 50), 26, 60
                    )
                    if self.lives <= 0:
                        self.lives = 0
                        self.state = "game_over"
                else:
                    self.gold += enemy.reward
                    self.kills += 1
                    sound_manager.play("gold")
                    self.effects.add_gold_text(enemy.x, enemy.y - 15, enemy.reward)
                    self.effects.add_death_explosion(enemy.x, enemy.y, enemy.color)

                    if enemy.can_split and not enemy.has_split:
                        split_enemies = enemy.get_split_enemies()
                        new_enemies.extend(split_enemies)

        self.enemies = [e for e in self.enemies if e.alive]
        self.enemies.extend(new_enemies)

        # Башни
        for tower in self.towers:
            tower.update(self.enemies, self.projectiles, self.effects)

        # Снаряды
        for proj in self.projectiles:
            proj.update()

            if not proj.alive and proj.target:
                self.effects.add_hit_effect(proj.target.x, proj.target.y, proj.color)
                sound_manager.play("hit")

                if proj.splash_radius > 0:
                    sound_manager.play("explosion")
                    self.effects.add_splash_ring(
                        proj.target.x, proj.target.y, proj.splash_radius, proj.color
                    )
                    for enemy in self.enemies:
                        if enemy is proj.target or not enemy.alive:
                            continue
                        dist = math.hypot(enemy.x - proj.target.x, enemy.y - proj.target.y)
                        if dist <= proj.splash_radius:
                            splash_damage = proj.damage * (1 - dist / proj.splash_radius) * 0.6
                            enemy.take_damage(splash_damage)
                            if proj.slow_amount > 0:
                                enemy.apply_slow(proj.slow_amount, proj.slow_duration)
                            if proj.dot_damage > 0:
                                enemy.apply_poison(proj.dot_damage, proj.dot_duration)

        self.projectiles = [p for p in self.projectiles if p.alive]
        self.effects.update()

    def get_cell_at_mouse(self, mouse_pos):
        mx, my = mouse_pos
        if mx >= GAME_WIDTH:
            return None
        col = mx // CELL_SIZE
        row = my // CELL_SIZE
        if 0 <= col < GAME_WIDTH // CELL_SIZE and 0 <= row < GAME_HEIGHT // CELL_SIZE:
            return col, row
        return None

    def get_tower_at_cell(self, col, row):
        for tower in self.towers:
            if tower.col == col and tower.row == row:
                return tower
        return None

    def handle_game_click(self, mouse_pos, button):
        mx, my = mouse_pos

        if mx >= GAME_WIDTH:
            # Кнопки башен
            for btn in self.sidebar.tower_buttons:
                if btn.is_clicked(mouse_pos, True):
                    if self.selected_tower_type == btn.tower_type:
                        self.selected_tower_type = None
                    else:
                        self.selected_tower_type = btn.tower_type
                    self.selected_placed_tower = None
                    self.sidebar.selected_tower_type = self.selected_tower_type
                    self.sidebar.selected_placed_tower = None
                    return

            # Кнопки способностей
            if self.sidebar.ability_airstrike.rect.collidepoint(mouse_pos):
                self.trigger_ability("airstrike")
                return
            if self.sidebar.ability_freeze.rect.collidepoint(mouse_pos):
                self.trigger_ability("freeze")
                return
            if self.sidebar.ability_gold.rect.collidepoint(mouse_pos):
                self.trigger_ability("gold")
                return

            if self.sidebar.start_wave_btn.is_clicked(mouse_pos, True):
                self.start_wave()
                return

            if self.sidebar.speed_btn.is_clicked(mouse_pos, True):
                if self.game_speed == SPEED_NORMAL:
                    self.game_speed = SPEED_FAST
                else:
                    self.game_speed = SPEED_NORMAL
                return

            if (self.sidebar.sell_btn.is_clicked(mouse_pos, True)
                    and self.selected_placed_tower):
                self.sell_tower(self.selected_placed_tower)
                return

            if (self.sidebar.upgrade_btn.is_clicked(mouse_pos, True)
                    and self.selected_placed_tower):
                self.upgrade_tower(self.selected_placed_tower)
                return
            return

        cell = self.get_cell_at_mouse(mouse_pos)
        if cell is None:
            return

        col, row = cell

        if button == 1:
            if self.selected_tower_type:
                if self.place_tower(col, row, self.selected_tower_type):
                    pass
                else:
                    tower = self.get_tower_at_cell(col, row)
                    if tower:
                        self.selected_placed_tower = tower
                        self.selected_tower_type = None
                        self.sidebar.selected_tower_type = None
                        self.sidebar.selected_placed_tower = tower
            else:
                tower = self.get_tower_at_cell(col, row)
                if tower:
                    self.selected_placed_tower = tower
                    self.sidebar.selected_placed_tower = tower
                else:
                    self.selected_placed_tower = None
                    self.sidebar.selected_placed_tower = None

        elif button == 3:
            self.selected_tower_type = None
            self.selected_placed_tower = None
            self.sidebar.selected_tower_type = None
            self.sidebar.selected_placed_tower = None

    def draw_game(self):
        """Отрисовка игры с эффектом тряски камеры"""
        shake_x, shake_y = self.effects.get_shake_offset()
        game_surf = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))

        # Карта
        game_surf.blit(self.map_surface, (0, 0))

        # Подсветка клетки
        if self.hover_cell and self.selected_tower_type:
            col, row = self.hover_cell
            hx = col * CELL_SIZE
            hy = row * CELL_SIZE
            buildable = is_buildable(col, row, self.current_level) and self.get_tower_at_cell(col, row) is None
            affordable = self.gold >= TOWER_STATS[self.selected_tower_type]["levels"][0]["cost"]

            if buildable and affordable:
                tower_range = TOWER_STATS[self.selected_tower_type]["levels"][0]["range"]
                center_x = hx + CELL_SIZE // 2
                center_y = hy + CELL_SIZE // 2
                range_surf = pygame.Surface((tower_range * 2 + 4, tower_range * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(range_surf, (255, 255, 255, 20),
                                 (tower_range + 2, tower_range + 2), tower_range)
                pygame.draw.circle(range_surf, (255, 255, 255, 40),
                                 (tower_range + 2, tower_range + 2), tower_range, 1)
                game_surf.blit(range_surf, (center_x - tower_range - 2, center_y - tower_range - 2))

                preview_color = TOWER_COLORS[self.selected_tower_type]
                s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(s, (*preview_color, 120), (3, 3, CELL_SIZE - 6, CELL_SIZE - 6), border_radius=5)
                pygame.draw.rect(s, (*preview_color, 200), (3, 3, CELL_SIZE - 6, CELL_SIZE - 6), 2, border_radius=5)
                game_surf.blit(s, (hx, hy))
            else:
                s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(s, (255, 50, 50, 80), (0, 0, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(s, (255, 50, 50, 150), (0, 0, CELL_SIZE, CELL_SIZE), 2)
                game_surf.blit(s, (hx, hy))

        # Башни
        for tower in self.towers:
            is_selected = tower is self.selected_placed_tower
            is_hovered = False
            if self.hover_cell and not self.selected_tower_type:
                if tower.col == self.hover_cell[0] and tower.row == self.hover_cell[1]:
                    is_hovered = True
            tower.draw(game_surf, selected=is_selected, hover=is_hovered)

        # Враги
        for enemy in self.enemies:
            enemy.draw(game_surf)

        # Снаряды
        for proj in self.projectiles:
            proj.draw(game_surf)

        # Эффекты
        self.effects.draw(game_surf)

        # Наложение поверхности игры с тряской
        self.screen.blit(game_surf, (shake_x, shake_y))

        # Перезарядка способностей для UI
        cooldowns = {
            "airstrike": self.cd_airstrike / self.max_cd_airstrike,
            "freeze": self.cd_freeze / self.max_cd_freeze,
            "gold": self.cd_gold / self.max_cd_gold,
        }

        # Отрисовка боковой панели
        self.sidebar.draw(self.screen, self.gold, self.lives, self.wave_num,
                          self.wave_active, self.selected_placed_tower, self.game_speed, cooldowns)

    def run(self):
        """Основной цикл"""
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False
            mouse_button = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == HIDE_KEY:
                        self.hide_window()
                        continue

                    if self.state == "menu":
                        pass

                    elif self.state == "level_select":
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            self.level_select_menu.prev_level()
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.level_select_menu.next_level()
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.current_level = self.level_select_menu.selected_level
                            self.reset_game()
                            self.state = "playing"
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "menu"

                    elif self.state == "settings":
                        if event.key == pygame.K_ESCAPE:
                            self.state = "menu"

                    elif self.state == "playing":
                        if event.key == PAUSE_KEY:
                            self.state = "paused"

                        # Способности Q, W, E
                        if event.key == pygame.K_q:
                            self.trigger_ability("airstrike")
                        elif event.key == pygame.K_w:
                            self.trigger_ability("freeze")
                        elif event.key == pygame.K_e:
                            self.trigger_ability("gold")

                        # Горячие клавиши 1-8
                        tower_types = list(TOWER_STATS.keys())
                        for i in range(8):
                            if event.key == pygame.K_1 + i and i < len(tower_types):
                                t_type = tower_types[i]
                                if self.selected_tower_type == t_type:
                                    self.selected_tower_type = None
                                else:
                                    self.selected_tower_type = t_type
                                self.selected_placed_tower = None
                                self.sidebar.selected_tower_type = self.selected_tower_type
                                self.sidebar.selected_placed_tower = None

                        if event.key == pygame.K_SPACE:
                            if not self.wave_active:
                                self.start_wave()

                    elif self.state == "paused":
                        if event.key == PAUSE_KEY:
                            self.state = "playing"

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_click = True
                    mouse_button = event.button

            # ОБНОВЛЕНИЕ
            if self.state == "menu":
                self.main_menu.update(mouse_pos)
                if mouse_click and mouse_button == 1:
                    if self.main_menu.play_btn.is_clicked(mouse_pos, True):
                        self.state = "level_select"
                    elif self.main_menu.settings_btn.is_clicked(mouse_pos, True):
                        self.state = "settings"
                    elif self.main_menu.quit_btn.is_clicked(mouse_pos, True):
                        self.running = False

            elif self.state == "level_select":
                self.level_select_menu.update(mouse_pos)
                if mouse_click and mouse_button == 1:
                    if self.level_select_menu.left_btn.is_clicked(mouse_pos, True):
                        self.level_select_menu.prev_level()
                    elif self.level_select_menu.right_btn.is_clicked(mouse_pos, True):
                        self.level_select_menu.next_level()
                    elif self.level_select_menu.play_btn.is_clicked(mouse_pos, True):
                        self.current_level = self.level_select_menu.selected_level
                        self.reset_game()
                        self.state = "playing"
                    elif self.level_select_menu.back_btn.is_clicked(mouse_pos, True):
                        self.state = "menu"

            elif self.state == "settings":
                self.settings_menu.update(mouse_pos)
                if mouse_click and mouse_button == 1:
                    if self.settings_menu.vol_btn.is_clicked(mouse_pos, True):
                        self.settings_menu.toggle_volume()
                    elif self.settings_menu.diff_btn.is_clicked(mouse_pos, True):
                        self.settings_menu.difficulty = (self.settings_menu.difficulty + 1) % 3
                    elif self.settings_menu.back_btn.is_clicked(mouse_pos, True):
                        self.state = "menu"

            elif self.state == "playing":
                self.hover_cell = self.get_cell_at_mouse(mouse_pos)
                self.sidebar.update(mouse_pos, self.gold)

                if mouse_click:
                    self.handle_game_click(mouse_pos, mouse_button)

                self.update_game()

            elif self.state == "paused":
                self.pause_menu.update(mouse_pos)
                if mouse_click and mouse_button == 1:
                    if self.pause_menu.resume_btn.is_clicked(mouse_pos, True):
                        self.state = "playing"
                    elif self.pause_menu.menu_btn.is_clicked(mouse_pos, True):
                        self.state = "menu"

            elif self.state == "game_over":
                self.game_over_screen.update(mouse_pos)
                if mouse_click and mouse_button == 1:
                    if self.game_over_screen.menu_btn.is_clicked(mouse_pos, True):
                        self.state = "menu"

            # ОТРИСОВКА
            if self.state == "menu":
                self.main_menu.draw(self.screen)

            elif self.state == "level_select":
                self.level_select_menu.draw(self.screen)

            elif self.state == "settings":
                self.settings_menu.draw(self.screen)

            elif self.state == "playing":
                self.draw_game()

            elif self.state == "paused":
                self.draw_game()
                self.pause_menu.draw(self.screen)

            elif self.state == "game_over":
                self.draw_game()
                self.game_over_screen.draw(self.screen, self.game_won, self.wave_num, self.kills)

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()