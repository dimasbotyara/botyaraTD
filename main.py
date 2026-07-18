# main.py — Главный файл, запуск игры

import pygame
import sys
import math
import random
import ctypes

from settings import *
from map_data import get_path, get_map, is_buildable
from tower import Tower
from enemy import Enemy
from projectile import Projectile
from wave import get_wave
from effects import EffectsManager
from ui import (Sidebar, MainMenu, SettingsMenu, PauseMenu, GameOverScreen)


class Game:
    """Основной класс игры"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # Состояния
        self.state = "menu"  # menu, settings, playing, paused, game_over
        self.hidden = False

        # UI
        self.main_menu = MainMenu()
        self.settings_menu = SettingsMenu()
        self.pause_menu = PauseMenu()
        self.game_over_screen = GameOverScreen()
        self.sidebar = Sidebar()

        # Игровые объекты
        self.reset_game()

        # Для скрытия окна
        self.hwnd = None
        try:
            self.hwnd = pygame.display.get_wm_info()["window"]
        except Exception:
            pass

        # Пре-рендер карты
        self.map_surface = None
        self._render_map_surface()

    def reset_game(self):
        """Сброс состояния игры"""
        self.path = get_path()
        self.game_map = get_map()

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

        self.selected_tower_type = None
        self.selected_placed_tower = None
        self.hover_cell = None

        self.sidebar.selected_tower_type = None
        self.sidebar.selected_placed_tower = None

        self._render_map_surface()

    def _render_map_surface(self):
        """Пре-рендер фона карты (вызывается один раз)"""
        self.map_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.map_surface.fill(GRASS_1)

        game_map = get_map()

        for row in range(len(game_map)):
            for col in range(len(game_map[0])):
                x = col * CELL_SIZE
                y = row * CELL_SIZE
                cell = game_map[row][col]

                if cell == 0:
                    # Трава с текстурой
                    color = GRASS_1 if (row + col) % 2 == 0 else GRASS_2
                    pygame.draw.rect(self.map_surface, color, (x, y, CELL_SIZE, CELL_SIZE))
                    # Травинки
                    random.seed(row * 100 + col)
                    for _ in range(3):
                        gx = x + random.randint(5, CELL_SIZE - 5)
                        gy = y + random.randint(5, CELL_SIZE - 5)
                        gl = random.randint(3, 7)
                        gc = random.choice([
                            (30, 100, 40),
                            (35, 115, 45),
                            (25, 90, 35),
                        ])
                        pygame.draw.line(self.map_surface, gc, (gx, gy), (gx + random.randint(-2, 2), gy - gl), 1)

                elif cell in (1, 2, 3):
                    # Дорога
                    pygame.draw.rect(self.map_surface, PATH_COLOR, (x, y, CELL_SIZE, CELL_SIZE))

                    # Текстура дороги
                    random.seed(row * 100 + col + 999)
                    for _ in range(4):
                        sx = x + random.randint(2, CELL_SIZE - 3)
                        sy = y + random.randint(2, CELL_SIZE - 3)
                        sc = (
                            PATH_COLOR[0] + random.randint(-15, 15),
                            PATH_COLOR[1] + random.randint(-15, 15),
                            PATH_COLOR[2] + random.randint(-15, 15),
                        )
                        sc = tuple(max(0, min(255, c)) for c in sc)
                        pygame.draw.circle(self.map_surface, sc, (sx, sy), random.randint(1, 2))

                    # Бордюры дороги
                    # Проверяем соседей чтобы рисовать границы
                    if row > 0 and game_map[row - 1][col] == 0:
                        pygame.draw.line(self.map_surface, PATH_BORDER, (x, y), (x + CELL_SIZE, y), 2)
                    if row < len(game_map) - 1 and game_map[row + 1][col] == 0:
                        pygame.draw.line(self.map_surface, PATH_BORDER, (x, y + CELL_SIZE - 1),
                                        (x + CELL_SIZE, y + CELL_SIZE - 1), 2)
                    if col > 0 and game_map[row][col - 1] == 0:
                        pygame.draw.line(self.map_surface, PATH_BORDER, (x, y), (x, y + CELL_SIZE), 2)
                    if col < len(game_map[0]) - 1 and game_map[row][col + 1] == 0:
                        pygame.draw.line(self.map_surface, PATH_BORDER, (x + CELL_SIZE - 1, y),
                                        (x + CELL_SIZE - 1, y + CELL_SIZE), 2)

        # Вход и выход
        path = get_path()
        if len(path) > 1:
            # Стрелка входа
            sx, sy = path[0]
            pygame.draw.polygon(self.map_surface, (50, 200, 80), [
                (sx - 5, sy - 8), (sx + 8, sy), (sx - 5, sy + 8)
            ])

            # База (выход)
            ex, ey = path[-1]
            pygame.draw.rect(self.map_surface, (200, 50, 50),
                           (ex - 12, ey - 12, 24, 24), border_radius=4)
            pygame.draw.rect(self.map_surface, (255, 80, 80),
                           (ex - 8, ey - 8, 16, 16), border_radius=3)
            # Крестик на базе
            pygame.draw.line(self.map_surface, (255, 200, 200), (ex - 5, ey - 5), (ex + 5, ey + 5), 2)
            pygame.draw.line(self.map_surface, (255, 200, 200), (ex + 5, ey - 5), (ex - 5, ey + 5), 2)

        # Стрелки направления на дороге
        for i in range(0, len(path) - 1, 4):
            ax, ay = path[i]
            bx, by = path[min(i + 1, len(path) - 1)]
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

        # Сетка (тонкая)
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

        # Сложность
        difficulty = self.settings_menu.difficulty
        if difficulty == 0:
            # Легко — меньше врагов
            cut = max(3, len(self.wave_queue) * 3 // 4)
            self.wave_queue = self.wave_queue[:cut]
        elif difficulty == 2:
            # Сложно — больше врагов
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

    def place_tower(self, col, row, tower_type):
        """Поставить башню"""
        cost = TOWER_STATS[tower_type]["levels"][0]["cost"]
        if self.gold < cost:
            return False
        if not is_buildable(col, row):
            return False

        # Проверяем что нет башни
        for t in self.towers:
            if t.col == col and t.row == row:
                return False

        tower = Tower(col, row, tower_type)
        self.towers.append(tower)
        self.gold -= cost

        # Эффект постройки
        px = col * CELL_SIZE + CELL_SIZE // 2
        py = row * CELL_SIZE + CELL_SIZE // 2
        self.effects.add_explosion(px, py, TOWER_COLORS[tower_type], count=10, speed=2, size=3, lifetime=20)

        return True

    def sell_tower(self, tower):
        """Продать башню"""
        sell_price = tower.get_sell_price()
        self.gold += sell_price

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

        # Эффект
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
        # === Спавн врагов ===
        if self.wave_active and self.wave_queue:
            self.spawn_timer -= 1
            if self.spawn_timer <= 0:
                enemy_type, delay = self.wave_queue.pop(0)
                self.spawn_enemy(enemy_type)
                self.spawn_timer = delay

        # === Проверка конца волны ===
        if self.wave_active and not self.wave_queue and not self.enemies:
            self.wave_active = False
            # Бонус за волну
            wave_bonus = 15 + self.wave_num * 3
            difficulty = self.settings_menu.difficulty
            if difficulty == 0:
                wave_bonus = int(wave_bonus * 1.5)
            elif difficulty == 2:
                wave_bonus = int(wave_bonus * 0.7)
            self.gold += wave_bonus
            self.effects.add_floating_text(
                GAME_WIDTH // 2, GAME_HEIGHT // 2 - 40,
                f"Волна {self.wave_num} пройдена! +{wave_bonus}g",
                (255, 215, 0), 30, 90
            )

            # Проверка победы
            if self.wave_num >= MAX_WAVES:
                self.game_won = True
                self.state = "game_over"

        # === Обновление врагов ===
        new_enemies = []
        for enemy in self.enemies:
            enemy.update(self.enemies)

            if not enemy.alive:
                if enemy.reached_end:
                    self.lives -= 1
                    self.effects.add_floating_text(
                        enemy.x, enemy.y, "-1 HP!", (255, 50, 50), 26, 60
                    )
                    if self.lives <= 0:
                        self.lives = 0
                        self.state = "game_over"
                else:
                    # Убит — награда
                    self.gold += enemy.reward
                    self.kills += 1
                    self.effects.add_gold_text(enemy.x, enemy.y - 15, enemy.reward)
                    self.effects.add_death_explosion(enemy.x, enemy.y, enemy.color)

                    # Делитель — создает мелких
                    if enemy.can_split and not enemy.has_split:
                        split_enemies = enemy.get_split_enemies()
                        new_enemies.extend(split_enemies)

        self.enemies = [e for e in self.enemies if e.alive]
        self.enemies.extend(new_enemies)

        # === Обновление башен ===
        for tower in self.towers:
            tower.update(self.enemies, self.projectiles, self.effects)

        # === Обновление снарядов ===
        for proj in self.projectiles:
            proj.update()

            if not proj.alive and proj.target:
                # Эффект попадания
                self.effects.add_hit_effect(proj.target.x, proj.target.y, proj.color)

                # Splash урон
                if proj.splash_radius > 0:
                    self.effects.add_splash_ring(
                        proj.target.x, proj.target.y, proj.splash_radius,
                        proj.color
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

        # === Обновление эффектов ===
        self.effects.update()

    def get_cell_at_mouse(self, mouse_pos):
        """Получить координаты клетки под мышью"""
        mx, my = mouse_pos
        if mx >= GAME_WIDTH:
            return None
        col = mx // CELL_SIZE
        row = my // CELL_SIZE
        if 0 <= col < GAME_WIDTH // CELL_SIZE and 0 <= row < GAME_HEIGHT // CELL_SIZE:
            return col, row
        return None

    def get_tower_at_cell(self, col, row):
        """Найти башню в клетке"""
        for tower in self.towers:
            if tower.col == col and tower.row == row:
                return tower
        return None

    def handle_game_click(self, mouse_pos, button):
        """Обработка клика в игре"""
        mx, my = mouse_pos

        # Клик по боковой панели
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

            # Кнопка старта волны
            if self.sidebar.start_wave_btn.is_clicked(mouse_pos, True):
                self.start_wave()
                return

            # Кнопка скорости
            if self.sidebar.speed_btn.is_clicked(mouse_pos, True):
                if self.game_speed == SPEED_NORMAL:
                    self.game_speed = SPEED_FAST
                else:
                    self.game_speed = SPEED_NORMAL
                return

            # Кнопка продажи
            if (self.sidebar.sell_btn.is_clicked(mouse_pos, True)
                    and self.selected_placed_tower):
                self.sell_tower(self.selected_placed_tower)
                return

            # Кнопка улучшения
            if (self.sidebar.upgrade_btn.is_clicked(mouse_pos, True)
                    and self.selected_placed_tower):
                self.upgrade_tower(self.selected_placed_tower)
                return

            return

        # Клик по игровому полю
        cell = self.get_cell_at_mouse(mouse_pos)
        if cell is None:
            return

        col, row = cell

        if button == 1:  # ЛКМ
            if self.selected_tower_type:
                # Попытка поставить башню
                if self.place_tower(col, row, self.selected_tower_type):
                    pass  # Успешно
                else:
                    # Может нажал на существующую башню
                    tower = self.get_tower_at_cell(col, row)
                    if tower:
                        self.selected_placed_tower = tower
                        self.selected_tower_type = None
                        self.sidebar.selected_tower_type = None
                        self.sidebar.selected_placed_tower = tower
            else:
                # Выделить/снять выделение башни
                tower = self.get_tower_at_cell(col, row)
                if tower:
                    self.selected_placed_tower = tower
                    self.sidebar.selected_placed_tower = tower
                else:
                    self.selected_placed_tower = None
                    self.sidebar.selected_placed_tower = None

        elif button == 3:  # ПКМ
            # Отменить выбор
            self.selected_tower_type = None
            self.selected_placed_tower = None
            self.sidebar.selected_tower_type = None
            self.sidebar.selected_placed_tower = None

    def draw_game(self):
        """Отрисовка игры"""
        # Карта
        self.screen.blit(self.map_surface, (0, 0))

        # Подсветка клетки под мышью
        if self.hover_cell and self.selected_tower_type:
            col, row = self.hover_cell
            hx = col * CELL_SIZE
            hy = row * CELL_SIZE
            buildable = is_buildable(col, row) and self.get_tower_at_cell(col, row) is None
            affordable = self.gold >= TOWER_STATS[self.selected_tower_type]["levels"][0]["cost"]

            if buildable and affordable:
                # Показать радиус
                tower_range = TOWER_STATS[self.selected_tower_type]["levels"][0]["range"]
                center_x = hx + CELL_SIZE // 2
                center_y = hy + CELL_SIZE // 2
                range_surf = pygame.Surface((tower_range * 2 + 4, tower_range * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(range_surf, (255, 255, 255, 20),
                                 (tower_range + 2, tower_range + 2), tower_range)
                pygame.draw.circle(range_surf, (255, 255, 255, 40),
                                 (tower_range + 2, tower_range + 2), tower_range, 1)
                self.screen.blit(range_surf, (center_x - tower_range - 2, center_y - tower_range - 2))

                # Превью башни
                preview_color = TOWER_COLORS[self.selected_tower_type]
                s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(s, (*preview_color, 120), (3, 3, CELL_SIZE - 6, CELL_SIZE - 6), border_radius=5)
                pygame.draw.rect(s, (*preview_color, 200), (3, 3, CELL_SIZE - 6, CELL_SIZE - 6), 2, border_radius=5)
                self.screen.blit(s, (hx, hy))
            else:
                # Красная подсветка
                s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(s, (255, 50, 50, 80), (0, 0, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(s, (255, 50, 50, 150), (0, 0, CELL_SIZE, CELL_SIZE), 2)
                self.screen.blit(s, (hx, hy))

        # Башни
        for tower in self.towers:
            is_selected = tower is self.selected_placed_tower
            is_hovered = False
            if self.hover_cell and not self.selected_tower_type:
                if tower.col == self.hover_cell[0] and tower.row == self.hover_cell[1]:
                    is_hovered = True
            tower.draw(self.screen, selected=is_selected, hover=is_hovered)

        # Враги
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # Снаряды
        for proj in self.projectiles:
            proj.draw(self.screen)

        # Эффекты
        self.effects.draw(self.screen)

        # Боковая панель
        self.sidebar.draw(self.screen, self.gold, self.lives, self.wave_num,
                         self.wave_active, self.selected_placed_tower, self.game_speed)

    def run(self):
        """Основной цикл"""
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False
            mouse_button = 0

            # === СОБЫТИЯ ===
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    # Скрытие окна — работает в любом состоянии
                    if event.key == HIDE_KEY:
                        self.hide_window()
                        continue

                    if self.state == "menu":
                        pass

                    elif self.state == "settings":
                        if event.key == pygame.K_ESCAPE:
                            self.state = "menu"

                    elif self.state == "playing":
                        if event.key == PAUSE_KEY:
                            self.state = "paused"

                        # Горячие клавиши башен 1-8
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

                        # Пробел — старт волны
                        if event.key == pygame.K_SPACE:
                            if not self.wave_active:
                                self.start_wave()

                    elif self.state == "paused":
                        if event.key == PAUSE_KEY:
                            self.state = "playing"

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_click = True
                    mouse_button = event.button

            # === ОБНОВЛЕНИЕ ===
            if self.state == "menu":
                self.main_menu.update(mouse_pos)
                if mouse_click and mouse_button == 1:
                    if self.main_menu.play_btn.is_clicked(mouse_pos, True):
                        self.reset_game()
                        self.state = "playing"
                    elif self.main_menu.settings_btn.is_clicked(mouse_pos, True):
                        self.state = "settings"
                    elif self.main_menu.quit_btn.is_clicked(mouse_pos, True):
                        self.running = False

            elif self.state == "settings":
                self.settings_menu.update(mouse_pos)
                if mouse_click and mouse_button == 1:
                    if self.settings_menu.diff_btn.is_clicked(mouse_pos, True):
                        self.settings_menu.difficulty = (self.settings_menu.difficulty + 1) % 3
                    elif self.settings_menu.back_btn.is_clicked(mouse_pos, True):
                        self.state = "menu"

            elif self.state == "playing":
                # Hover
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

            # === ОТРИСОВКА ===
            if self.state == "menu":
                self.main_menu.draw(self.screen)

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