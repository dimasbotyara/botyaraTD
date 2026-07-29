# ui.py — Интерфейс: боковая панель, супер-способности, Geometry Dash выбор уровня, меню

import pygame
import math
from settings import *
from map_data import LEVEL_DATA, get_path
from sound import sound_manager


class Button:
    """Универсальная кнопка с анимацией наведения"""

    def __init__(self, x, y, width, height, text, color, hover_color,
                 text_color=WHITE, font_size=22, border_radius=8):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.Font(None, font_size)
        self.border_radius = border_radius
        self.hovered = False
        self.enabled = True
        self.visible = True

    def update(self, mouse_pos):
        if self.visible and self.enabled:
            self.hovered = self.rect.collidepoint(mouse_pos)
        else:
            self.hovered = False

    def is_clicked(self, mouse_pos, mouse_click):
        if self.visible and self.enabled and self.hovered and mouse_click:
            sound_manager.play("click")
            return True
        return False

    def draw(self, surface):
        if not self.visible:
            return

        color = self.hover_color if self.hovered else self.color
        if not self.enabled:
            color = DARK_GRAY

        # Тень
        shadow_rect = self.rect.copy()
        shadow_rect.y += 2
        pygame.draw.rect(surface, (0, 0, 0, 80), shadow_rect, border_radius=self.border_radius)

        # Кнопка
        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)

        # Обводка
        border_color = (min(255, color[0] + 30), min(255, color[1] + 30), min(255, color[2] + 30))
        pygame.draw.rect(surface, border_color, self.rect, 1, border_radius=self.border_radius)

        # Текст
        text_surf = self.font.render(self.text, True, self.text_color if self.enabled else GRAY)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class TowerButton:
    """Кнопка выбора башни в панели"""

    def __init__(self, x, y, width, height, tower_type):
        self.rect = pygame.Rect(x, y, width, height)
        self.tower_type = tower_type
        self.stats = TOWER_STATS[tower_type]
        self.color = TOWER_COLORS[tower_type]
        self.color_dark = TOWER_COLORS_DARK[tower_type]
        self.hovered = False
        self.selected = False
        self.affordable = True

        self.name_font = pygame.font.Font(None, 20)
        self.cost_font = pygame.font.Font(None, 18)
        self.desc_font = pygame.font.Font(None, 16)

    def update(self, mouse_pos, gold):
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.affordable = gold >= self.stats["levels"][0]["cost"]

    def is_clicked(self, mouse_pos, mouse_click):
        if self.hovered and mouse_click and self.affordable:
            sound_manager.play("click")
            return True
        return False

    def draw(self, surface):
        if self.selected:
            bg_color = UI_SELECTED
        elif self.hovered and self.affordable:
            bg_color = UI_HOVER
        else:
            bg_color = UI_PANEL

        pygame.draw.rect(surface, bg_color, self.rect, border_radius=6)

        if not self.affordable:
            dark_overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            dark_overlay.fill((0, 0, 0, 80))
            surface.blit(dark_overlay, self.rect.topleft)

        border_col = self.color if self.selected else UI_BORDER
        pygame.draw.rect(surface, border_col, self.rect, 2, border_radius=6)

        icon_x = self.rect.x + 18
        icon_y = self.rect.y + self.rect.height // 2
        pygame.draw.rect(surface, self.color_dark,
                         (icon_x - 8, icon_y - 8, 16, 16), border_radius=3)
        pygame.draw.rect(surface, self.color,
                         (icon_x - 6, icon_y - 6, 12, 12), border_radius=2)

        name_surf = self.name_font.render(self.stats["name"], True, WHITE)
        surface.blit(name_surf, (icon_x + 14, self.rect.y + 5))

        desc_surf = self.desc_font.render(self.stats["desc"], True, GRAY)
        surface.blit(desc_surf, (icon_x + 14, self.rect.y + 22))

        cost = self.stats["levels"][0]["cost"]
        cost_color = GOLD_COLOR if self.affordable else HP_RED
        cost_surf = self.cost_font.render(f"{cost}g", True, cost_color)
        surface.blit(cost_surf, (self.rect.right - cost_surf.get_width() - 8, self.rect.y + 5))


class AbilityButton:
    """Кнопка супер-способности игрока"""

    def __init__(self, x, y, width, height, ability_key, name, key_hint, cost, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.ability_key = ability_key
        self.name = name
        self.key_hint = key_hint
        self.cost = cost
        self.color = color
        self.hovered = False
        self.font = pygame.font.Font(None, 17)

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface, cooldown_ratio, gold):
        affordable = gold >= self.cost and cooldown_ratio <= 0
        bg_col = (60, 60, 90) if self.hovered and affordable else UI_PANEL
        
        pygame.draw.rect(surface, bg_col, self.rect, border_radius=6)
        border_col = self.color if affordable else UI_BORDER
        pygame.draw.rect(surface, border_col, self.rect, 2, border_radius=6)

        # Текст
        txt_col = WHITE if affordable else GRAY
        surf = self.font.render(f"{self.name} ({self.key_hint}) - {self.cost}g", True, txt_col)
        surface.blit(surf, (self.rect.x + 6, self.rect.y + 6))

        # Оверлей перезарядки (Cooldown bar)
        if cooldown_ratio > 0:
            cd_w = int(self.rect.width * cooldown_ratio)
            cd_surf = pygame.Surface((cd_w, self.rect.height), pygame.SRCALPHA)
            cd_surf.fill((0, 0, 0, 160))
            surface.blit(cd_surf, (self.rect.x, self.rect.y))


class Sidebar:
    """Боковая панель с башнями и способностями"""

    def __init__(self):
        self.x = GAME_WIDTH
        self.width = SIDEBAR_WIDTH
        self.height = WINDOW_HEIGHT

        self.title_font = pygame.font.Font(None, 28)
        self.info_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)

        # Кнопки башен
        self.tower_buttons = []
        tower_types = list(TOWER_STATS.keys())
        btn_h = 38
        start_y = 145
        padding = 3

        for i, t_type in enumerate(tower_types):
            by = start_y + i * (btn_h + padding)
            self.tower_buttons.append(
                TowerButton(self.x + 8, by, self.width - 16, btn_h, t_type)
            )

        # Кнопки супер-способностей
        ab_y = start_y + len(tower_types) * (btn_h + padding) + 6
        self.ability_airstrike = AbilityButton(self.x + 8, ab_y, self.width - 16, 26, "airstrike", "💣 Авиаудар", "Q", 100, (255, 100, 50))
        self.ability_freeze = AbilityButton(self.x + 8, ab_y + 29, self.width - 16, 26, "freeze", "❄️ Заморозка", "W", 50, (100, 200, 255))
        self.ability_gold = AbilityButton(self.x + 8, ab_y + 58, self.width - 16, 26, "gold", "💰 Лихорадка", "E", 0, (255, 215, 0))

        # Кнопки управления
        btn_area_y = ab_y + 92

        self.start_wave_btn = Button(
            self.x + 8, btn_area_y, self.width - 16, 36,
            "НАЧАТЬ ВОЛНУ", BTN_GREEN, BTN_GREEN_HOVER, font_size=22
        )

        self.speed_btn = Button(
            self.x + 8, btn_area_y + 40, self.width - 16, 28,
            "x1 Скорость", BTN_BLUE, BTN_BLUE_HOVER, font_size=19
        )

        self.sell_btn = Button(
            self.x + 8, btn_area_y + 72, (self.width - 20) // 2, 28,
            "Продать", BTN_RED, BTN_RED_HOVER, font_size=17
        )
        self.sell_btn.visible = False

        self.upgrade_btn = Button(
            self.x + 12 + (self.width - 20) // 2, btn_area_y + 72,
            (self.width - 20) // 2, 28,
            "Улучшить", BTN_YELLOW, BTN_YELLOW_HOVER,
            text_color=BLACK, font_size=17
        )
        self.upgrade_btn.visible = False

        self.selected_tower_type = None
        self.selected_placed_tower = None

    def update(self, mouse_pos, gold):
        for btn in self.tower_buttons:
            btn.update(mouse_pos, gold)
        self.ability_airstrike.update(mouse_pos)
        self.ability_freeze.update(mouse_pos)
        self.ability_gold.update(mouse_pos)
        self.start_wave_btn.update(mouse_pos)
        self.speed_btn.update(mouse_pos)
        self.sell_btn.update(mouse_pos)
        self.upgrade_btn.update(mouse_pos)

    def draw(self, surface, gold, lives, wave_num, wave_active, selected_tower=None, game_speed=1, cooldowns=None):
        if cooldowns is None:
            cooldowns = {"airstrike": 0, "freeze": 0, "gold": 0}

        panel_rect = pygame.Rect(self.x, 0, self.width, self.height)
        pygame.draw.rect(surface, UI_BG, panel_rect)
        pygame.draw.line(surface, UI_BORDER, (self.x, 0), (self.x, self.height), 2)

        # Заголовок
        title_surf = self.title_font.render("botyaraTD", True, WHITE)
        surface.blit(title_surf, (self.x + self.width // 2 - title_surf.get_width() // 2, 8))

        pygame.draw.line(surface, UI_BORDER, (self.x + 10, 32), (self.x + self.width - 10, 32), 1)

        # Статистика игрока
        wave_text = f"Волна: {wave_num}/{MAX_WAVES}"
        wave_surf = self.info_font.render(wave_text, True, WHITE)
        surface.blit(wave_surf, (self.x + 12, 38))

        lives_color = HP_GREEN if lives > 10 else (HP_YELLOW if lives > 5 else HP_RED)
        lives_surf = self.info_font.render(f"Жизни: {lives}", True, lives_color)
        surface.blit(lives_surf, (self.x + 12, 60))

        # Полоска жизней
        bar_x = self.x + 12
        bar_y = 78
        bar_w = self.width - 24
        bar_h = 6
        pygame.draw.rect(surface, HP_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fill_w = int(bar_w * (lives / START_LIVES))
        if fill_w > 0:
            pygame.draw.rect(surface, lives_color, (bar_x, bar_y, fill_w, bar_h), border_radius=3)

        gold_surf = self.info_font.render(f"Золото: {gold}", True, GOLD_COLOR)
        surface.blit(gold_surf, (self.x + 12, 90))

        pygame.draw.line(surface, UI_BORDER, (self.x + 10, 112), (self.x + self.width - 10, 112), 1)

        towers_title = self.small_font.render("БАШНИ (1-8):", True, LIGHT_GRAY)
        surface.blit(towers_title, (self.x + 12, 120))

        # Отрисовка кнопок башен
        for i, btn in enumerate(self.tower_buttons):
            btn.selected = (btn.tower_type == self.selected_tower_type)
            btn.draw(surface)
            key_surf = self.small_font.render(str(i + 1), True, GRAY)
            surface.blit(key_surf, (btn.rect.x + 3, btn.rect.y + 3))

        # Отрисовка способностей
        self.ability_airstrike.draw(surface, cooldowns.get("airstrike", 0), gold)
        self.ability_freeze.draw(surface, cooldowns.get("freeze", 0), gold)
        self.ability_gold.draw(surface, cooldowns.get("gold", 0), gold)

        # Отрисовка кнопок волны и скорости
        if wave_active:
            self.start_wave_btn.text = "ВОЛНА ИДЁТ..."
            self.start_wave_btn.enabled = False
        else:
            self.start_wave_btn.text = "НАЧАТЬ ВОЛНУ"
            self.start_wave_btn.enabled = True
        self.start_wave_btn.draw(surface)

        self.speed_btn.text = f"x{game_speed} Скорость"
        self.speed_btn.draw(surface)

        # Отрисовка информации о выбранной башне
        if selected_tower:
            self.sell_btn.visible = True
            self.upgrade_btn.visible = True

            info_y = self.sell_btn.rect.bottom + 6
            name = f"{selected_tower.name} (Ур.{selected_tower.level + 1})"
            name_surf = self.info_font.render(name, True, selected_tower.color)
            surface.blit(name_surf, (self.x + 12, info_y))

            stats_texts = [
                f"Урон: {selected_tower.damage:.1f}",
                f"Скор: {60 / max(1, selected_tower.fire_rate):.1f}/с",
                f"Радиус: {selected_tower.range}",
            ]

            for i, text in enumerate(stats_texts):
                s = self.small_font.render(text, True, LIGHT_GRAY)
                surface.blit(s, (self.x + 12, info_y + 20 + i * 14))

            upgrade_cost = selected_tower.get_upgrade_cost()
            if upgrade_cost is not None:
                self.upgrade_btn.text = f"Up {upgrade_cost}g"
                self.upgrade_btn.enabled = True
            else:
                self.upgrade_btn.text = "MAX"
                self.upgrade_btn.enabled = False

            self.sell_btn.text = f"Продать"
        else:
            self.sell_btn.visible = False
            self.upgrade_btn.visible = False

        self.sell_btn.draw(surface)
        self.upgrade_btn.draw(surface)


class LevelSelectMenu:
    """ Geometry Dash Style Карусель вы выбора 5 уровней """

    def __init__(self):
        self.title_font = pygame.font.Font(None, 65)
        self.card_title_font = pygame.font.Font(None, 40)
        self.diff_font = pygame.font.Font(None, 26)
        self.desc_font = pygame.font.Font(None, 20)

        self.selected_level = 0  # 0..4

        # Кнопки карусели
        card_w, card_h = 560, 420
        card_x = WINDOW_WIDTH // 2 - card_w // 2
        card_y = WINDOW_HEIGHT // 2 - card_h // 2 + 10

        self.card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

        # Стрелки управления (слева и справа от карточки)
        self.left_btn = Button(card_x - 75, card_y + card_h // 2 - 40, 60, 80, "<",
                               BTN_BLUE, BTN_BLUE_HOVER, font_size=50, border_radius=12)
        self.right_btn = Button(card_x + card_w + 15, card_y + card_h // 2 - 40, 60, 80, ">",
                                BTN_BLUE, BTN_BLUE_HOVER, font_size=50, border_radius=12)

        self.play_btn = Button(card_x + card_w // 2 - 120, card_y + card_h - 65, 240, 48,
                               "ИГРАТЬ УРОВЕНЬ", BTN_GREEN, BTN_GREEN_HOVER, font_size=26)
        
        self.back_btn = Button(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT - 55, 200, 40,
                               "НАЗАД В МЕНЮ", BTN_RED, BTN_RED_HOVER, font_size=22)

        self.timer = 0

    def next_level(self):
        self.selected_level = (self.selected_level + 1) % len(LEVEL_DATA)
        sound_manager.play("click")

    def prev_level(self):
        self.selected_level = (self.selected_level - 1) % len(LEVEL_DATA)
        sound_manager.play("click")

    def update(self, mouse_pos):
        self.left_btn.update(mouse_pos)
        self.right_btn.update(mouse_pos)
        self.play_btn.update(mouse_pos)
        self.back_btn.update(mouse_pos)
        self.timer += 1

    def draw(self, surface):
        surface.fill((15, 15, 25))

        # Заголовок
        title = self.title_font.render("ВЫБОР УРОВНЯ", True, WHITE)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 25))

        lvl_info = LEVEL_DATA[self.selected_level]

        # Отрисовка Главной Карточки Уровня (Geometry Dash Style)
        card = self.card_rect
        pygame.draw.rect(surface, UI_PANEL, card, border_radius=18)

        # Эффект свечения границы уровня в зависимости от его темы
        glow_color = lvl_info["border_color"]
        pygame.draw.rect(surface, glow_color, card, 3, border_radius=18)

        # Название уровня
        name_surf = self.card_title_font.render(lvl_info["name"], True, WHITE)
        surface.blit(name_surf, (card.centerx - name_surf.get_width() // 2, card.y + 20))

        # Плашка сложности
        diff_colors = {
            "Легко": (60, 200, 80),
            "Нормально": (255, 200, 50),
            "Сложно": (255, 120, 40),
            "Эксперт": (200, 50, 255),
            "Апокалипсис": (255, 40, 40),
        }
        diff_col = diff_colors.get(lvl_info["diff"], GOLD_COLOR)
        diff_surf = self.diff_font.render(f"Сложность: {lvl_info['diff']}", True, diff_col)
        surface.blit(diff_surf, (card.centerx - diff_surf.get_width() // 2, card.y + 60))

        # Мини-карта / Превью уровня
        thumb_w, thumb_h = 320, 180
        thumb_x = card.centerx - thumb_w // 2
        thumb_y = card.y + 95

        thumb_surf = pygame.Surface((thumb_w, thumb_h))
        thumb_surf.fill(lvl_info["bg_color"])

        # Отрисовка уменьшенной сетки дороги
        grid = lvl_info["grid"]
        rows = len(grid)
        cols = len(grid[0])
        cw = thumb_w / cols
        ch = thumb_h / rows

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] in (1, 2, 3):
                    cell_rect = pygame.Rect(c * cw, r * ch, cw + 1, ch + 1)
                    pygame.draw.rect(thumb_surf, lvl_info["path_color"], cell_rect)

        pygame.draw.rect(surface, (0, 0, 0), (thumb_x - 2, thumb_y - 2, thumb_w + 4, thumb_h + 4), border_radius=6)
        surface.blit(thumb_surf, (thumb_x, thumb_y))
        pygame.draw.rect(surface, glow_color, (thumb_x, thumb_y, thumb_w, thumb_h), 2, border_radius=6)

        # Описание уровня
        desc_surf = self.desc_font.render(lvl_info["desc"], True, LIGHT_GRAY)
        surface.blit(desc_surf, (card.centerx - desc_surf.get_width() // 2, thumb_y + thumb_h + 15))

        # Точки-индикаторы карусели уровня (Dots Indicator)
        dots_y = card.bottom - 80
        for i in range(len(LEVEL_DATA)):
            dot_x = card.centerx - (len(LEVEL_DATA) * 16) // 2 + i * 16 + 8
            dot_color = GOLD_COLOR if i == self.selected_level else DARK_GRAY
            dot_radius = 5 if i == self.selected_level else 3
            pygame.draw.circle(surface, dot_color, (dot_x, dots_y), dot_radius)

        # Отрисовка кнопок
        self.left_btn.draw(surface)
        self.right_btn.draw(surface)
        self.play_btn.draw(surface)
        self.back_btn.draw(surface)


class MainMenu:
    """Главное меню"""

    def __init__(self):
        self.title_font = pygame.font.Font(None, 80)
        self.subtitle_font = pygame.font.Font(None, 30)

        btn_w, btn_h = 280, 50
        center_x = WINDOW_WIDTH // 2 - btn_w // 2

        self.play_btn = Button(center_x, 320, btn_w, btn_h, "ВЫБОР УРОВНЯ",
                               BTN_GREEN, BTN_GREEN_HOVER, font_size=30)
        self.settings_btn = Button(center_x, 385, btn_w, btn_h, "НАСТРОЙКИ",
                                   BTN_BLUE, BTN_BLUE_HOVER, font_size=30)
        self.quit_btn = Button(center_x, 450, btn_w, btn_h, "ВЫХОД",
                               BTN_RED, BTN_RED_HOVER, font_size=30)

        self.timer = 0

    def update(self, mouse_pos):
        self.play_btn.update(mouse_pos)
        self.settings_btn.update(mouse_pos)
        self.quit_btn.update(mouse_pos)
        self.timer += 1

    def draw(self, surface):
        surface.fill((15, 15, 25))

        for i in range(20):
            x = int(WINDOW_WIDTH / 2 + math.cos(self.timer * 0.01 + i * 0.5) * (200 + i * 20))
            y = int(WINDOW_HEIGHT / 2 + math.sin(self.timer * 0.013 + i * 0.7) * (150 + i * 10))
            alpha = int(30 + 20 * math.sin(self.timer * 0.02 + i))
            size = int(3 + 2 * math.sin(self.timer * 0.03 + i * 0.3))
            color_val = int(60 + 40 * math.sin(self.timer * 0.015 + i * 0.5))
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (color_val, color_val, color_val + 40, alpha), (size, size), size)
            surface.blit(s, (x - size, y - size))

        title_text = "botyaraTD"
        shadow = self.title_font.render(title_text, True, (0, 0, 0))
        surface.blit(shadow, (WINDOW_WIDTH // 2 - shadow.get_width() // 2 + 3, 103))

        pulse = math.sin(self.timer * 0.05) * 0.5 + 0.5
        r = int(100 + 155 * pulse)
        g = int(150 + 50 * (1 - pulse))
        b = int(200 + 55 * pulse)
        title_surf = self.title_font.render(title_text, True, (r, g, b))
        surface.blit(title_surf, (WINDOW_WIDTH // 2 - title_surf.get_width() // 2, 100))

        sub = self.subtitle_font.render("Deluxe Edition & 5 Levels", True, GRAY)
        surface.blit(sub, (WINDOW_WIDTH // 2 - sub.get_width() // 2, 175))

        line_y = 220
        line_w = 300
        pygame.draw.line(surface, UI_BORDER,
                         (WINDOW_WIDTH // 2 - line_w // 2, line_y),
                         (WINDOW_WIDTH // 2 + line_w // 2, line_y), 2)

        desc_lines = [
            "5 карт | 8 типов башен | Супер-способности",
            "Процедурный звук | Сочные визуальные эффекты",
        ]
        for i, line in enumerate(desc_lines):
            desc_surf = self.subtitle_font.render(line, True, LIGHT_GRAY)
            surface.blit(desc_surf, (WINDOW_WIDTH // 2 - desc_surf.get_width() // 2, 240 + i * 30))

        self.play_btn.draw(surface)
        self.settings_btn.draw(surface)
        self.quit_btn.draw(surface)

        ver = self.subtitle_font.render("v2.0 | Deluxe Pygame", True, DARK_GRAY)
        surface.blit(ver, (WINDOW_WIDTH // 2 - ver.get_width() // 2, WINDOW_HEIGHT - 40))


class SettingsMenu:
    """Меню настроек"""

    def __init__(self):
        self.title_font = pygame.font.Font(None, 50)
        self.info_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)

        center_x = WINDOW_WIDTH // 2
        self.volume_level = 0.5
        self.difficulty = 1
        self.diff_names = ["Легко", "Нормально", "Сложно"]

        btn_w = 260
        self.vol_btn = Button(center_x - btn_w // 2, 220, btn_w, 40,
                              f"Громкость: {int(self.volume_level * 100)}%",
                              BTN_BLUE, BTN_BLUE_HOVER, font_size=22)

        self.diff_btn = Button(center_x - btn_w // 2, 280, btn_w, 40,
                               f"Сложность: {self.diff_names[self.difficulty]}",
                               BTN_BLUE, BTN_BLUE_HOVER, font_size=22)

        self.back_btn = Button(center_x - btn_w // 2, 450, btn_w, 45,
                               "НАЗАД", BTN_RED, BTN_RED_HOVER, font_size=26)

    def toggle_volume(self):
        self.volume_level = (self.volume_level + 0.25)
        if self.volume_level > 1.05:
            self.volume_level = 0.0
        sound_manager.set_volume(self.volume_level)

    def update(self, mouse_pos):
        self.vol_btn.text = f"Громкость: {int(self.volume_level * 100)}%"
        self.vol_btn.update(mouse_pos)
        self.diff_btn.update(mouse_pos)
        self.back_btn.update(mouse_pos)

    def draw(self, surface):
        surface.fill((15, 15, 25))

        title = self.title_font.render("НАСТРОЙКИ", True, WHITE)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 80))

        pygame.draw.line(surface, UI_BORDER,
                         (WINDOW_WIDTH // 2 - 150, 130),
                         (WINDOW_WIDTH // 2 + 150, 130), 2)

        self.vol_btn.draw(surface)
        self.diff_btn.text = f"Сложность: {self.diff_names[self.difficulty]}"
        self.diff_btn.draw(surface)

        controls_title = self.info_font.render("Управление:", True, LIGHT_GRAY)
        surface.blit(controls_title, (WINDOW_WIDTH // 2 - controls_title.get_width() // 2, 350))

        controls = [
            "1-8 — Выбор башни  |  Q, W, E — Супер-способности",
            "Стрелки ЛЕВО / ПРАВО — Навигация в выборе уровня",
            "ESC — Пауза / Назад  |  F9 — Скрыть окно",
        ]
        for i, ctrl in enumerate(controls):
            c_surf = self.small_font.render(ctrl, True, GRAY)
            surface.blit(c_surf, (WINDOW_WIDTH // 2 - c_surf.get_width() // 2, 385 + i * 20))

        self.back_btn.draw(surface)


class PauseMenu:
    """Меню паузы"""

    def __init__(self):
        self.title_font = pygame.font.Font(None, 60)
        self.info_font = pygame.font.Font(None, 24)

        center_x = WINDOW_WIDTH // 2
        btn_w = 240

        self.resume_btn = Button(center_x - btn_w // 2, 320, btn_w, 45,
                                 "ПРОДОЛЖИТЬ", BTN_GREEN, BTN_GREEN_HOVER, font_size=26)
        self.menu_btn = Button(center_x - btn_w // 2, 380, btn_w, 45,
                               "В МЕНЮ", BTN_RED, BTN_RED_HOVER, font_size=26)

    def update(self, mouse_pos):
        self.resume_btn.update(mouse_pos)
        self.menu_btn.update(mouse_pos)

    def draw(self, surface):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        box_w, box_h = 350, 250
        box_x = WINDOW_WIDTH // 2 - box_w // 2
        box_y = WINDOW_HEIGHT // 2 - box_h // 2
        pygame.draw.rect(surface, UI_BG, (box_x, box_y, box_w, box_h), border_radius=15)
        pygame.draw.rect(surface, UI_BORDER, (box_x, box_y, box_w, box_h), 2, border_radius=15)

        title = self.title_font.render("ПАУЗА", True, WHITE)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, box_y + 30))

        hint = self.info_font.render("ESC - продолжить", True, GRAY)
        surface.blit(hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, box_y + 85))

        self.resume_btn.draw(surface)
        self.menu_btn.draw(surface)


class GameOverScreen:
    """Экран конца игры"""

    def __init__(self):
        self.title_font = pygame.font.Font(None, 70)
        self.info_font = pygame.font.Font(None, 30)
        self.timer = 0

        center_x = WINDOW_WIDTH // 2
        btn_w = 240

        self.menu_btn = Button(center_x - btn_w // 2, 430, btn_w, 45,
                               "В МЕНЮ", BTN_BLUE, BTN_BLUE_HOVER, font_size=26)

    def update(self, mouse_pos):
        self.menu_btn.update(mouse_pos)
        self.timer += 1

    def draw(self, surface, won, wave_reached, kills):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        box_w, box_h = 450, 320
        box_x = WINDOW_WIDTH // 2 - box_w // 2
        box_y = WINDOW_HEIGHT // 2 - box_h // 2

        border_color = BTN_GREEN if won else BTN_RED
        pygame.draw.rect(surface, UI_BG, (box_x, box_y, box_w, box_h), border_radius=15)
        pygame.draw.rect(surface, border_color, (box_x, box_y, box_w, box_h), 3, border_radius=15)

        if won:
            title_text = "ПОБЕДА!"
            title_color = (50, 255, 100)
        else:
            title_text = "ПОРАЖЕНИЕ"
            title_color = (255, 80, 80)

        pulse = math.sin(self.timer * 0.08) * 10
        title = self.title_font.render(title_text, True, title_color)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, box_y + 30 + int(pulse * 0.3)))

        stats = [
            f"Волна: {wave_reached}/{MAX_WAVES}",
            f"Убийств: {kills}",
        ]

        for i, stat in enumerate(stats):
            stat_surf = self.info_font.render(stat, True, WHITE)
            surface.blit(stat_surf, (WINDOW_WIDTH // 2 - stat_surf.get_width() // 2, box_y + 120 + i * 35))

        if won:
            congrats = self.info_font.render("Ты защитил базу!", True, GOLD_COLOR)
            surface.blit(congrats, (WINDOW_WIDTH // 2 - congrats.get_width() // 2, box_y + 220))
        else:
            tip = self.info_font.render("Попробуй другую стратегию!", True, GRAY)
            surface.blit(tip, (WINDOW_WIDTH // 2 - tip.get_width() // 2, box_y + 220))

        self.menu_btn.draw(surface)