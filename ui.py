# ui.py — Интерфейс: боковая панель, кнопки, меню

import pygame
import math
from settings import *


class Button:
    """Универсальная кнопка"""

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
        return self.visible and self.enabled and self.hovered and mouse_click

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
        return self.hovered and mouse_click and self.affordable

    def draw(self, surface):
        # Фон
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

        # Обводка
        border_col = self.color if self.selected else UI_BORDER
        pygame.draw.rect(surface, border_col, self.rect, 2, border_radius=6)

        # Миниатюра башни
        icon_x = self.rect.x + 18
        icon_y = self.rect.y + self.rect.height // 2
        pygame.draw.rect(surface, self.color_dark,
                         (icon_x - 8, icon_y - 8, 16, 16), border_radius=3)
        pygame.draw.rect(surface, self.color,
                         (icon_x - 6, icon_y - 6, 12, 12), border_radius=2)

        # Название
        name_surf = self.name_font.render(self.stats["name"], True, WHITE)
        surface.blit(name_surf, (icon_x + 14, self.rect.y + 5))

        # Описание
        desc_surf = self.desc_font.render(self.stats["desc"], True, GRAY)
        surface.blit(desc_surf, (icon_x + 14, self.rect.y + 22))

        # Цена
        cost = self.stats["levels"][0]["cost"]
        cost_color = GOLD_COLOR if self.affordable else HP_RED
        cost_surf = self.cost_font.render(f"{cost}g", True, cost_color)
        surface.blit(cost_surf, (self.rect.right - cost_surf.get_width() - 8, self.rect.y + 5))


class Sidebar:
    """Боковая панель"""

    def __init__(self):
        self.x = GAME_WIDTH
        self.width = SIDEBAR_WIDTH
        self.height = WINDOW_HEIGHT

        self.title_font = pygame.font.Font(None, 30)
        self.info_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)
        self.big_font = pygame.font.Font(None, 36)

        # Кнопки башен
        self.tower_buttons = []
        tower_types = list(TOWER_STATS.keys())
        btn_h = 42
        start_y = 170
        padding = 4

        for i, t_type in enumerate(tower_types):
            by = start_y + i * (btn_h + padding)
            self.tower_buttons.append(
                TowerButton(self.x + 8, by, self.width - 16, btn_h, t_type)
            )

        # Кнопки управления
        btn_area_y = start_y + len(tower_types) * (btn_h + padding) + 10

        self.start_wave_btn = Button(
            self.x + 8, btn_area_y, self.width - 16, 36,
            "НАЧАТЬ ВОЛНУ", BTN_GREEN, BTN_GREEN_HOVER, font_size=22
        )

        self.speed_btn = Button(
            self.x + 8, btn_area_y + 42, self.width - 16, 30,
            "x1 Скорость", BTN_BLUE, BTN_BLUE_HOVER, font_size=20
        )

        self.sell_btn = Button(
            self.x + 8, btn_area_y + 78, (self.width - 20) // 2, 30,
            "Продать", BTN_RED, BTN_RED_HOVER, font_size=18
        )
        self.sell_btn.visible = False

        self.upgrade_btn = Button(
            self.x + 12 + (self.width - 20) // 2, btn_area_y + 78,
            (self.width - 20) // 2, 30,
            "Улучшить", BTN_YELLOW, BTN_YELLOW_HOVER,
            text_color=BLACK, font_size=18
        )
        self.upgrade_btn.visible = False

        self.selected_tower_type = None
        self.selected_placed_tower = None

    def update(self, mouse_pos, gold):
        for btn in self.tower_buttons:
            btn.update(mouse_pos, gold)
        self.start_wave_btn.update(mouse_pos)
        self.speed_btn.update(mouse_pos)
        self.sell_btn.update(mouse_pos)
        self.upgrade_btn.update(mouse_pos)

    def draw(self, surface, gold, lives, wave_num, wave_active, selected_tower=None, game_speed=1):
        # Фон панели
        panel_rect = pygame.Rect(self.x, 0, self.width, self.height)
        pygame.draw.rect(surface, UI_BG, panel_rect)
        pygame.draw.line(surface, UI_BORDER, (self.x, 0), (self.x, self.height), 2)

        # === Заголовок ===
        title_surf = self.title_font.render("TOWER DEFENSE", True, WHITE)
        surface.blit(title_surf, (self.x + self.width // 2 - title_surf.get_width() // 2, 10))

        # Разделитель
        pygame.draw.line(surface, UI_BORDER, (self.x + 10, 38), (self.x + self.width - 10, 38), 1)

        # === Инфо ===
        # Волна
        wave_text = f"Волна: {wave_num}/{MAX_WAVES}"
        wave_surf = self.info_font.render(wave_text, True, WHITE)
        surface.blit(wave_surf, (self.x + 12, 48))

        # Жизни
        lives_color = HP_GREEN if lives > 10 else (HP_YELLOW if lives > 5 else HP_RED)
        lives_surf = self.info_font.render(f"Жизни: {lives}", True, lives_color)
        surface.blit(lives_surf, (self.x + 12, 72))

        # Полоска жизней
        bar_x = self.x + 12
        bar_y = 92
        bar_w = self.width - 24
        bar_h = 8
        pygame.draw.rect(surface, HP_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill_w = int(bar_w * (lives / START_LIVES))
        if fill_w > 0:
            pygame.draw.rect(surface, lives_color, (bar_x, bar_y, fill_w, bar_h), border_radius=4)

        # Золото
        gold_surf = self.info_font.render(f"Золото: {gold}", True, GOLD_COLOR)
        surface.blit(gold_surf, (self.x + 12, 108))

        # Разделитель
        pygame.draw.line(surface, UI_BORDER, (self.x + 10, 132), (self.x + self.width - 10, 132), 1)

        # Подзаголовок
        towers_title = self.small_font.render("БАШНИ:", True, LIGHT_GRAY)
        surface.blit(towers_title, (self.x + 12, 140))

        # Подсветка горячих клавиш
        hotkeys = self.small_font.render("(1-8)", True, GRAY)
        surface.blit(hotkeys, (self.x + 62, 140))

        # === Кнопки башен ===
        for i, btn in enumerate(self.tower_buttons):
            btn.selected = (btn.tower_type == self.selected_tower_type)
            btn.draw(surface)
            # Горячая клавиша
            key_surf = self.small_font.render(str(i + 1), True, GRAY)
            surface.blit(key_surf, (btn.rect.x + 3, btn.rect.y + 3))

        # === Кнопки управления ===
        # Старт волны
        if wave_active:
            self.start_wave_btn.text = "ВОЛНА ИДЁТ..."
            self.start_wave_btn.enabled = False
        else:
            self.start_wave_btn.text = "НАЧАТЬ ВОЛНУ"
            self.start_wave_btn.enabled = True
        self.start_wave_btn.draw(surface)

        # Скорость
        self.speed_btn.text = f"x{game_speed} Скорость"
        self.speed_btn.draw(surface)

        # === Инфо о выбранной башне ===
        if selected_tower:
            self.sell_btn.visible = True
            self.upgrade_btn.visible = True

            info_y = self.sell_btn.rect.bottom + 10

            # Название и уровень
            name = f"{selected_tower.name} (Ур.{selected_tower.level + 1})"
            name_surf = self.info_font.render(name, True, selected_tower.color)
            surface.blit(name_surf, (self.x + 12, info_y))

            # Статы
            stats_texts = [
                f"Урон: {selected_tower.damage:.1f}",
                f"Скор.: {60 / max(1, selected_tower.fire_rate):.1f}/с",
                f"Радиус: {selected_tower.range}",
            ]

            if selected_tower.slow_amount > 0:
                stats_texts.append(f"Замедл.: {int(selected_tower.slow_amount * 100)}%")
            if selected_tower.splash_radius > 0:
                stats_texts.append(f"AOE: {selected_tower.splash_radius}")
            if selected_tower.dot_damage > 0:
                stats_texts.append(f"Яд: {selected_tower.dot_damage}/с")
            if selected_tower.chain_count > 0:
                stats_texts.append(f"Цепь: {selected_tower.chain_count}")

            for i, text in enumerate(stats_texts):
                s = self.small_font.render(text, True, LIGHT_GRAY)
                surface.blit(s, (self.x + 12, info_y + 22 + i * 16))

            # Цена продажи
            sell_text = f"Продажа: {selected_tower.get_sell_price()}g"
            sell_surf = self.small_font.render(sell_text, True, (200, 100, 100))
            surface.blit(sell_surf, (self.x + 12, info_y + 22 + len(stats_texts) * 16 + 4))

            # Обновить текст кнопки улучшения
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

        # === Подсказки внизу ===
        bottom_y = self.height - 50
        pygame.draw.line(surface, UI_BORDER, (self.x + 10, bottom_y - 5),
                         (self.x + self.width - 10, bottom_y - 5), 1)

        hints = [
            "ESC - Пауза",
            "F9 - Скрыть",
        ]
        for i, hint in enumerate(hints):
            hint_surf = self.small_font.render(hint, True, GRAY)
            surface.blit(hint_surf, (self.x + 12, bottom_y + i * 18))


class MainMenu:
    """Главное меню"""

    def __init__(self):
        self.title_font = pygame.font.Font(None, 80)
        self.subtitle_font = pygame.font.Font(None, 30)

        btn_w, btn_h = 280, 50
        center_x = WINDOW_WIDTH // 2 - btn_w // 2

        self.play_btn = Button(center_x, 320, btn_w, btn_h, "ИГРАТЬ",
                               BTN_GREEN, BTN_GREEN_HOVER, font_size=30)
        self.settings_btn = Button(center_x, 385, btn_w, btn_h, "НАСТРОЙКИ",
                                   BTN_BLUE, BTN_BLUE_HOVER, font_size=30)
        self.quit_btn = Button(center_x, 450, btn_w, btn_h, "ВЫХОД",
                               BTN_RED, BTN_RED_HOVER, font_size=30)

        self.particles = []
        self.timer = 0

    def update(self, mouse_pos):
        self.play_btn.update(mouse_pos)
        self.settings_btn.update(mouse_pos)
        self.quit_btn.update(mouse_pos)
        self.timer += 1

    def draw(self, surface):
        surface.fill((15, 15, 25))

        # Фоновые декорации
        import math
        for i in range(20):
            x = int(WINDOW_WIDTH / 2 + math.cos(self.timer * 0.01 + i * 0.5) * (200 + i * 20))
            y = int(WINDOW_HEIGHT / 2 + math.sin(self.timer * 0.013 + i * 0.7) * (150 + i * 10))
            alpha = int(30 + 20 * math.sin(self.timer * 0.02 + i))
            size = int(3 + 2 * math.sin(self.timer * 0.03 + i * 0.3))
            color_val = int(60 + 40 * math.sin(self.timer * 0.015 + i * 0.5))
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (color_val, color_val, color_val + 40, alpha), (size, size), size)
            surface.blit(s, (x - size, y - size))

        # Заголовок
        title_text = "TOWER DEFENSE"
        # Тень
        shadow = self.title_font.render(title_text, True, (0, 0, 0))
        surface.blit(shadow, (WINDOW_WIDTH // 2 - shadow.get_width() // 2 + 3, 103))

        # Градиентное свечение через смену цвета
        pulse = math.sin(self.timer * 0.05) * 0.5 + 0.5
        r = int(100 + 155 * pulse)
        g = int(150 + 50 * (1 - pulse))
        b = int(200 + 55 * pulse)
        title_surf = self.title_font.render(title_text, True, (r, g, b))
        surface.blit(title_surf, (WINDOW_WIDTH // 2 - title_surf.get_width() // 2, 100))

        # Подзаголовок
        sub = self.subtitle_font.render("Deluxe Edition", True, GRAY)
        surface.blit(sub, (WINDOW_WIDTH // 2 - sub.get_width() // 2, 175))

        # Декоративная линия
        line_y = 220
        line_w = 300
        pygame.draw.line(surface, UI_BORDER,
                         (WINDOW_WIDTH // 2 - line_w // 2, line_y),
                         (WINDOW_WIDTH // 2 + line_w // 2, line_y), 2)

        # Описание
        desc_lines = [
            "8 типов башен | 10 видов врагов | 25 волн",
            "Улучшения | Эффекты | Боссы",
        ]
        for i, line in enumerate(desc_lines):
            desc_surf = self.subtitle_font.render(line, True, LIGHT_GRAY)
            surface.blit(desc_surf, (WINDOW_WIDTH // 2 - desc_surf.get_width() // 2, 240 + i * 30))

        # Кнопки
        self.play_btn.draw(surface)
        self.settings_btn.draw(surface)
        self.quit_btn.draw(surface)

        # Версия
        ver = self.subtitle_font.render("v1.0 | pygame", True, DARK_GRAY)
        surface.blit(ver, (WINDOW_WIDTH // 2 - ver.get_width() // 2, WINDOW_HEIGHT - 40))


class SettingsMenu:
    """Меню настроек"""

    def __init__(self):
        self.title_font = pygame.font.Font(None, 50)
        self.info_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)

        center_x = WINDOW_WIDTH // 2

        self.volume_label = "Громкость: (без звука)"
        self.difficulty = 1  # 0 = легко, 1 = нормально, 2 = сложно
        self.diff_names = ["Легко", "Нормально", "Сложно"]

        btn_w = 220
        self.diff_btn = Button(center_x - btn_w // 2, 280, btn_w, 40,
                               f"Сложность: {self.diff_names[self.difficulty]}",
                               BTN_BLUE, BTN_BLUE_HOVER, font_size=22)

        self.back_btn = Button(center_x - btn_w // 2, 450, btn_w, 45,
                               "НАЗАД", BTN_RED, BTN_RED_HOVER, font_size=26)

    def update(self, mouse_pos):
        self.diff_btn.update(mouse_pos)
        self.back_btn.update(mouse_pos)

    def draw(self, surface):
        surface.fill((15, 15, 25))

        title = self.title_font.render("НАСТРОЙКИ", True, WHITE)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 80))

        pygame.draw.line(surface, UI_BORDER,
                         (WINDOW_WIDTH // 2 - 150, 130),
                         (WINDOW_WIDTH // 2 + 150, 130), 2)

        # Громкость (заглушка)
        vol_surf = self.info_font.render(self.volume_label, True, GRAY)
        surface.blit(vol_surf, (WINDOW_WIDTH // 2 - vol_surf.get_width() // 2, 200))

        # Сложность
        self.diff_btn.text = f"Сложность: {self.diff_names[self.difficulty]}"
        self.diff_btn.draw(surface)

        # Описание сложности
        diff_descs = [
            "Больше золота, меньше врагов",
            "Стандартный баланс",
            "Меньше золота, больше врагов, враги сильнее"
        ]
        desc_surf = self.small_font.render(diff_descs[self.difficulty], True, GRAY)
        surface.blit(desc_surf, (WINDOW_WIDTH // 2 - desc_surf.get_width() // 2, 330))

        # Управление
        controls_title = self.info_font.render("Управление:", True, LIGHT_GRAY)
        surface.blit(controls_title, (WINDOW_WIDTH // 2 - controls_title.get_width() // 2, 370))

        controls = [
            "1-8 — Выбор башни  |  ЛКМ — Поставить",
            "ESC — Пауза  |  F9 — Скрыть окно",
        ]
        for i, ctrl in enumerate(controls):
            c_surf = self.small_font.render(ctrl, True, GRAY)
            surface.blit(c_surf, (WINDOW_WIDTH // 2 - c_surf.get_width() // 2, 400 + i * 20))

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
        # Затемнение
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Рамка
        box_w, box_h = 350, 250
        box_x = WINDOW_WIDTH // 2 - box_w // 2
        box_y = WINDOW_HEIGHT // 2 - box_h // 2
        pygame.draw.rect(surface, UI_BG, (box_x, box_y, box_w, box_h), border_radius=15)
        pygame.draw.rect(surface, UI_BORDER, (box_x, box_y, box_w, box_h), 2, border_radius=15)

        # Заголовок
        title = self.title_font.render("ПАУЗА", True, WHITE)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, box_y + 30))

        # Подсказка
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

        # Рамка
        box_w, box_h = 450, 320
        box_x = WINDOW_WIDTH // 2 - box_w // 2
        box_y = WINDOW_HEIGHT // 2 - box_h // 2

        border_color = BTN_GREEN if won else BTN_RED
        pygame.draw.rect(surface, UI_BG, (box_x, box_y, box_w, box_h), border_radius=15)
        pygame.draw.rect(surface, border_color, (box_x, box_y, box_w, box_h), 3, border_radius=15)

        # Заголовок
        if won:
            title_text = "ПОБЕДА!"
            title_color = (50, 255, 100)
        else:
            title_text = "ПОРАЖЕНИЕ"
            title_color = (255, 80, 80)

        import math
        pulse = math.sin(self.timer * 0.08) * 10
        title = self.title_font.render(title_text, True, title_color)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, box_y + 30 + int(pulse * 0.3)))

        # Статистика
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