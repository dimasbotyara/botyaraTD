# ui.py — Интерфейс: мультиязычность (RU/EN), векторые иконки, карусель уровней с блокировкой

import pygame
import math
from settings import *
from map_data import LEVEL_DATA, get_path
from sound import sound_manager
from highscores import highscore_manager
from config import t, config_manager
from icons import (draw_bomb_icon, draw_ice_icon, draw_gold_icon,
                   draw_trophy_icon, draw_lock_icon, draw_star_icon)


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

        shadow_rect = self.rect.copy()
        shadow_rect.y += 2
        pygame.draw.rect(surface, (0, 0, 0, 80), shadow_rect, border_radius=self.border_radius)

        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)

        border_color = (min(255, color[0] + 30), min(255, color[1] + 30), min(255, color[2] + 30))
        pygame.draw.rect(surface, border_color, self.rect, 1, border_radius=self.border_radius)

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
    """Кнопка супер-способности игрока с отрисовкой иконки"""

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

        # Отрисовка векторной иконки
        icon_x = self.rect.x + 4
        icon_y = self.rect.y + (self.rect.height - 18) // 2
        if self.ability_key == "airstrike":
            draw_bomb_icon(surface, icon_x, icon_y, 18)
        elif self.ability_key == "freeze":
            draw_ice_icon(surface, icon_x, icon_y, 18)
        elif self.ability_key == "gold":
            draw_gold_icon(surface, icon_x, icon_y, 18)

        txt_col = WHITE if affordable else GRAY
        disp_name = t(f"ability_{self.ability_key}").split()[-1]  # Берём чистое название без префикса
        surf = self.font.render(f"{disp_name} ({self.key_hint}) - {self.cost}g", True, txt_col)
        surface.blit(surf, (self.rect.x + 26, self.rect.y + 6))

        if cooldown_ratio > 0:
            cd_w = int(self.rect.width * cooldown_ratio)
            cd_surf = pygame.Surface((cd_w, self.rect.height), pygame.SRCALPHA)
            cd_surf.fill((0, 0, 0, 160))
            surface.blit(cd_surf, (self.rect.x, self.rect.y))


class InWorldTowerMenu:
    """Всплывающее меню прокачки прямо над выделенной башней на карте"""

    def __init__(self):
        self.width = 210
        self.height = 70
        self.font_title = pygame.font.Font(None, 19)
        self.font_btn = pygame.font.Font(None, 18)
        self.font_stat = pygame.font.Font(None, 16)
        self.upgrade_hover = False
        self.sell_hover = False

    def get_rect(self, tower):
        x = max(10, min(GAME_WIDTH - self.width - 10, tower.x - self.width // 2))
        y = tower.y - CELL_SIZE // 2 - self.height - 12
        if y < 10:
            y = tower.y + CELL_SIZE // 2 + 12
        return pygame.Rect(x, y, self.width, self.height)

    def get_buttons_rects(self, menu_rect):
        btn_w = (menu_rect.width - 16) // 2
        btn_h = 24
        up_rect = pygame.Rect(menu_rect.x + 6, menu_rect.bottom - btn_h - 6, btn_w, btn_h)
        sell_rect = pygame.Rect(menu_rect.x + 10 + btn_w, menu_rect.bottom - btn_h - 6, btn_w, btn_h)
        return up_rect, sell_rect

    def update(self, mouse_pos, tower):
        if not tower:
            return
        menu_rect = self.get_rect(tower)
        up_rect, sell_rect = self.get_buttons_rects(menu_rect)
        self.upgrade_hover = up_rect.collidepoint(mouse_pos)
        self.sell_hover = sell_rect.collidepoint(mouse_pos)

    def check_click(self, mouse_pos, tower, gold):
        if not tower:
            return None
        menu_rect = self.get_rect(tower)
        up_rect, sell_rect = self.get_buttons_rects(menu_rect)

        if up_rect.collidepoint(mouse_pos):
            cost = tower.get_upgrade_cost()
            if cost is not None and gold >= cost:
                return "upgrade"
        elif sell_rect.collidepoint(mouse_pos):
            return "sell"
        return None

    def draw(self, surface, tower, gold):
        if not tower:
            return

        menu_rect = self.get_rect(tower)
        up_rect, sell_rect = self.get_buttons_rects(menu_rect)

        pygame.draw.rect(surface, UI_BG, menu_rect, border_radius=10)
        pygame.draw.rect(surface, GOLD_COLOR, menu_rect, 2, border_radius=10)

        level_str = f"Lvl {tower.level + 1}"
        if tower.level < 2:
            level_str += " -> " + str(tower.level + 2)
        title_surf = self.font_title.render(f"{tower.name} ({level_str})", True, WHITE)
        surface.blit(title_surf, (menu_rect.x + 8, menu_rect.y + 5))

        lvl_data = tower.stats_data["levels"]
        if tower.level < 2:
            next_dmg = lvl_data[tower.level + 1]["damage"]
            stat_str = f"{t('damage')}: {tower.damage:.0f} -> {next_dmg}"
        else:
            stat_str = f"{t('damage')}: {tower.damage:.0f} ({t('max')})"
        stat_surf = self.font_stat.render(stat_str, True, LIGHT_GRAY)
        surface.blit(stat_surf, (menu_rect.x + 8, menu_rect.y + 22))

        cost = tower.get_upgrade_cost()
        if cost is not None:
            can_afford = gold >= cost
            up_col = BTN_GREEN_HOVER if self.upgrade_hover and can_afford else (BTN_GREEN if can_afford else DARK_GRAY)
            up_txt = f"Up {cost}g"
        else:
            can_afford = False
            up_col = DARK_GRAY
            up_txt = t("max")

        pygame.draw.rect(surface, up_col, up_rect, border_radius=5)
        txt_surf = self.font_btn.render(up_txt, True, WHITE if can_afford else GRAY)
        surface.blit(txt_surf, txt_surf.get_rect(center=up_rect.center))

        sell_price = tower.get_sell_price()
        sell_col = BTN_RED_HOVER if self.sell_hover else BTN_RED
        pygame.draw.rect(surface, sell_col, sell_rect, border_radius=5)
        sell_surf = self.font_btn.render(f"+{sell_price}g", True, WHITE)
        surface.blit(sell_surf, sell_surf.get_rect(center=sell_rect.center))


class Sidebar:
    """Боковая панель с информацией и кнопками"""

    def __init__(self):
        self.x = GAME_WIDTH
        self.width = SIDEBAR_WIDTH
        self.height = WINDOW_HEIGHT

        self.title_font = pygame.font.Font(None, 28)
        self.info_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)
        self.card_font = pygame.font.Font(None, 20)

        self.tower_buttons = []
        tower_types = list(TOWER_STATS.keys())
        btn_h = 38
        start_y = 135
        padding = 3

        for i, t_type in enumerate(tower_types):
            by = start_y + i * (btn_h + padding)
            self.tower_buttons.append(
                TowerButton(self.x + 8, by, self.width - 16, btn_h, t_type)
            )

        ab_y = start_y + len(tower_types) * (btn_h + padding) + 4
        self.ability_airstrike = AbilityButton(self.x + 8, ab_y, self.width - 16, 25, "airstrike", "Airstrike", "Q", 100, (255, 100, 50))
        self.ability_freeze = AbilityButton(self.x + 8, ab_y + 28, self.width - 16, 25, "freeze", "Freeze", "W", 50, (100, 200, 255))
        self.ability_gold = AbilityButton(self.x + 8, ab_y + 56, self.width - 16, 25, "gold", "Gold Rush", "E", 0, (255, 215, 0))

        btn_area_y = ab_y + 88

        self.start_wave_btn = Button(
            self.x + 8, btn_area_y, self.width - 16, 36,
            t("start_wave"), BTN_GREEN, BTN_GREEN_HOVER, font_size=22
        )

        self.speed_btn = Button(
            self.x + 8, btn_area_y + 40, self.width - 16, 28,
            f"x1 {t('speed')}", BTN_BLUE, BTN_BLUE_HOVER, font_size=19
        )

        self.sell_btn = Button(
            self.x + 8, btn_area_y + 72, (self.width - 20) // 2, 28,
            t("sell"), BTN_RED, BTN_RED_HOVER, font_size=17
        )

        self.upgrade_btn = Button(
            self.x + 12 + (self.width - 20) // 2, btn_area_y + 72,
            (self.width - 20) // 2, 28,
            t("upgrade"), BTN_YELLOW, BTN_YELLOW_HOVER,
            text_color=BLACK, font_size=17
        )

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

        title_surf = self.title_font.render(t("title"), True, WHITE)
        surface.blit(title_surf, (self.x + self.width // 2 - title_surf.get_width() // 2, 8))

        pygame.draw.line(surface, UI_BORDER, (self.x + 10, 32), (self.x + self.width - 10, 32), 1)

        wave_text = f"{t('wave')}: {wave_num}/{MAX_WAVES}"
        wave_surf = self.info_font.render(wave_text, True, WHITE)
        surface.blit(wave_surf, (self.x + 12, 38))

        lives_color = HP_GREEN if lives > 10 else (HP_YELLOW if lives > 5 else HP_RED)
        lives_surf = self.info_font.render(f"{t('lives')}: {lives}", True, lives_color)
        surface.blit(lives_surf, (self.x + 12, 58))

        bar_x = self.x + 12
        bar_y = 76
        bar_w = self.width - 24
        bar_h = 6
        pygame.draw.rect(surface, HP_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fill_w = int(bar_w * (lives / START_LIVES))
        if fill_w > 0:
            pygame.draw.rect(surface, lives_color, (bar_x, bar_y, fill_w, bar_h), border_radius=3)

        gold_surf = self.info_font.render(f"{t('gold')}: {gold}", True, GOLD_COLOR)
        surface.blit(gold_surf, (self.x + 12, 86))

        pygame.draw.line(surface, UI_BORDER, (self.x + 10, 108), (self.x + self.width - 10, 108), 1)

        towers_title = self.small_font.render(f"{t('towers')} (1-8):", True, LIGHT_GRAY)
        surface.blit(towers_title, (self.x + 12, 114))

        for i, btn in enumerate(self.tower_buttons):
            btn.selected = (btn.tower_type == self.selected_tower_type)
            btn.draw(surface)
            key_surf = self.small_font.render(str(i + 1), True, GRAY)
            surface.blit(key_surf, (btn.rect.x + 3, btn.rect.y + 3))

        self.ability_airstrike.draw(surface, cooldowns.get("airstrike", 0), gold)
        self.ability_freeze.draw(surface, cooldowns.get("freeze", 0), gold)
        self.ability_gold.draw(surface, cooldowns.get("gold", 0), gold)

        if wave_active:
            self.start_wave_btn.text = t("wave_in_progress")
            self.start_wave_btn.enabled = False
        else:
            self.start_wave_btn.text = t("start_wave")
            self.start_wave_btn.enabled = True
        self.start_wave_btn.draw(surface)

        self.speed_btn.text = f"x{game_speed} {t('speed')}"
        self.speed_btn.draw(surface)

        if selected_tower:
            self.sell_btn.visible = True
            self.upgrade_btn.visible = True

            info_y = self.sell_btn.rect.bottom + 6
            name = f"{selected_tower.name} (Lvl {selected_tower.level + 1})"
            name_surf = self.card_font.render(name, True, selected_tower.color)
            surface.blit(name_surf, (self.x + 12, info_y))

            lvl_data = selected_tower.stats_data["levels"]
            if selected_tower.level < 2:
                next_lvl = lvl_data[selected_tower.level + 1]
                stats_texts = [
                    f"{t('damage')}: {selected_tower.damage:.0f} -> {next_lvl['damage']}",
                    f"{t('range')}: {selected_tower.range} -> {next_lvl['range']}",
                ]
            else:
                stats_texts = [
                    f"{t('damage')}: {selected_tower.damage:.0f} ({t('max')})",
                    f"{t('range')}: {selected_tower.range} ({t('max')})",
                ]

            for i, text in enumerate(stats_texts):
                s = self.small_font.render(text, True, LIGHT_GRAY)
                surface.blit(s, (self.x + 12, info_y + 18 + i * 14))

            upgrade_cost = selected_tower.get_upgrade_cost()
            if upgrade_cost is not None:
                self.upgrade_btn.text = f"Up {upgrade_cost}g"
                self.upgrade_btn.enabled = True
            else:
                self.upgrade_btn.text = t("max")
                self.upgrade_btn.enabled = False

            self.sell_btn.text = t("sell")
            self.sell_btn.draw(surface)
            self.upgrade_btn.draw(surface)
        else:
            self.sell_btn.visible = False
            self.upgrade_btn.visible = False
            hint_surf = self.small_font.render(t("hint_upgrade"), True, GRAY)
            surface.blit(hint_surf, (self.x + 12, self.height - 30))


class LevelSelectMenu:
    """ Карусель выбора 5 уровней с блокировкой замков и векторными иконками """

    def __init__(self):
        self.title_font = pygame.font.Font(None, 65)
        self.card_title_font = pygame.font.Font(None, 40)
        self.diff_font = pygame.font.Font(None, 26)
        self.desc_font = pygame.font.Font(None, 20)
        self.score_font = pygame.font.Font(None, 22)

        self.selected_level = 0

        card_w, card_h = 560, 420
        card_x = WINDOW_WIDTH // 2 - card_w // 2
        card_y = WINDOW_HEIGHT // 2 - card_h // 2 + 10

        self.card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

        self.left_btn = Button(card_x - 75, card_y + card_h // 2 - 40, 60, 80, "<",
                               BTN_BLUE, BTN_BLUE_HOVER, font_size=50, border_radius=12)
        self.right_btn = Button(card_x + card_w + 15, card_y + card_h // 2 - 40, 60, 80, ">",
                                BTN_BLUE, BTN_BLUE_HOVER, font_size=50, border_radius=12)

        self.play_btn = Button(card_x + card_w // 2 - 140, card_y + card_h - 60, 280, 48,
                               t("play_level"), BTN_GREEN, BTN_GREEN_HOVER, font_size=24)
        
        self.back_btn = Button(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT - 55, 200, 40,
                               t("back_to_menu"), BTN_RED, BTN_RED_HOVER, font_size=22)

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
        self.play_btn.text = t("play_level")
        self.back_btn.text = t("back_to_menu")
        
        is_unlocked = highscore_manager.is_level_unlocked(self.selected_level)
        if not is_unlocked:
            self.play_btn.enabled = False
            self.play_btn.text = t("locked")
        else:
            self.play_btn.enabled = True

        self.play_btn.update(mouse_pos)
        self.back_btn.update(mouse_pos)
        self.timer += 1

    def draw(self, surface):
        surface.fill((15, 15, 25))

        title = self.title_font.render(t("level_select"), True, WHITE)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 25))

        lvl_info = LEVEL_DATA[self.selected_level]
        score_info = highscore_manager.get_score(self.selected_level)
        is_unlocked = highscore_manager.is_level_unlocked(self.selected_level)

        card = self.card_rect
        pygame.draw.rect(surface, UI_PANEL, card, border_radius=18)

        glow_color = lvl_info["border_color"] if is_unlocked else (80, 80, 80)
        pygame.draw.rect(surface, glow_color, card, 3, border_radius=18)

        name_surf = self.card_title_font.render(lvl_info["name"], True, WHITE if is_unlocked else GRAY)
        surface.blit(name_surf, (card.centerx - name_surf.get_width() // 2, card.y + 15))

        diff_key = f"diff_{self.selected_level}"
        diff_str = t(diff_key)
        diff_surf = self.diff_font.render(f"{t('difficulty')}: {diff_str}", True, GOLD_COLOR if is_unlocked else GRAY)
        surface.blit(diff_surf, (card.centerx - diff_surf.get_width() // 2, card.y + 50))

        # Отрисовка Векторных Звёзд Рекорда
        stars_cnt = 0
        if score_info["completed"]:
            stars_cnt = 3
        elif score_info["best_wave"] >= 15:
            stars_cnt = 2
        elif score_info["best_wave"] >= 5:
            stars_cnt = 1

        stars_start_x = card.centerx - 30
        for s_idx in range(3):
            draw_star_icon(surface, stars_start_x + s_idx * 22, card.y + 75, 18, filled=(s_idx < stars_cnt))

        # Превью уровня
        thumb_w, thumb_h = 300, 150
        thumb_x = card.centerx - thumb_w // 2
        thumb_y = card.y + 105

        thumb_surf = pygame.Surface((thumb_w, thumb_h))
        thumb_surf.fill(lvl_info["bg_color"])

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

        if not is_unlocked:
            lock_overlay = pygame.Surface((card.width, card.height), pygame.SRCALPHA)
            lock_overlay.fill((0, 0, 0, 180))
            surface.blit(lock_overlay, card.topleft)

            draw_lock_icon(surface, card.centerx - 12, card.centery - 45, 24)

            lock_text = self.card_title_font.render(t("locked"), True, (255, 80, 80))
            surface.blit(lock_text, (card.centerx - lock_text.get_width() // 2, card.centery - 15))

            pass_text = self.desc_font.render(t("pass_prev"), True, LIGHT_GRAY)
            surface.blit(pass_text, (card.centerx - pass_text.get_width() // 2, card.centery + 18))

        else:
            desc_surf = self.desc_font.render(lvl_info["desc"], True, LIGHT_GRAY)
            surface.blit(desc_surf, (card.centerx - desc_surf.get_width() // 2, thumb_y + thumb_h + 8))

            draw_trophy_icon(surface, card.centerx - 110, thumb_y + thumb_h + 26, 18)

            rec_text = f"{t('record')}: {score_info['best_wave']}/{MAX_WAVES}  |  {t('kills')}: {score_info['best_kills']}"
            rec_surf = self.score_font.render(rec_text, True, GOLD_COLOR)
            surface.blit(rec_surf, (card.centerx - rec_surf.get_width() // 2 + 10, thumb_y + thumb_h + 26))

        dots_y = card.bottom - 75
        for i in range(len(LEVEL_DATA)):
            dot_x = card.centerx - (len(LEVEL_DATA) * 16) // 2 + i * 16 + 8
            dot_color = GOLD_COLOR if i == self.selected_level else DARK_GRAY
            dot_radius = 5 if i == self.selected_level else 3
            pygame.draw.circle(surface, dot_color, (dot_x, dots_y), dot_radius)

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

        self.play_btn = Button(center_x, 320, btn_w, btn_h, t("play"),
                               BTN_GREEN, BTN_GREEN_HOVER, font_size=30)
        self.settings_btn = Button(center_x, 385, btn_w, btn_h, t("settings"),
                                   BTN_BLUE, BTN_BLUE_HOVER, font_size=30)
        self.quit_btn = Button(center_x, 450, btn_w, btn_h, t("quit"),
                               BTN_RED, BTN_RED_HOVER, font_size=30)

        self.timer = 0

    def update(self, mouse_pos):
        self.play_btn.text = t("play")
        self.settings_btn.text = t("settings")
        self.quit_btn.text = t("quit")

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

        title_text = t("title")
        shadow = self.title_font.render(title_text, True, (0, 0, 0))
        surface.blit(shadow, (WINDOW_WIDTH // 2 - shadow.get_width() // 2 + 3, 103))

        pulse = math.sin(self.timer * 0.05) * 0.5 + 0.5
        r = int(100 + 155 * pulse)
        g = int(150 + 50 * (1 - pulse))
        b = int(200 + 55 * pulse)
        title_surf = self.title_font.render(title_text, True, (r, g, b))
        surface.blit(title_surf, (WINDOW_WIDTH // 2 - title_surf.get_width() // 2, 100))

        sub = self.subtitle_font.render(t("subtitle"), True, GRAY)
        surface.blit(sub, (WINDOW_WIDTH // 2 - sub.get_width() // 2, 175))

        line_y = 220
        line_w = 300
        pygame.draw.line(surface, UI_BORDER,
                         (WINDOW_WIDTH // 2 - line_w // 2, line_y),
                         (WINDOW_WIDTH // 2 + line_w // 2, line_y), 2)

        desc_lines = [
            "5 Level Campaign | 8 Tower Types | Super Abilities",
            "Custom Audio Support | Juicy Visuals",
        ]
        for i, line in enumerate(desc_lines):
            desc_surf = self.subtitle_font.render(line, True, LIGHT_GRAY)
            surface.blit(desc_surf, (WINDOW_WIDTH // 2 - desc_surf.get_width() // 2, 240 + i * 30))

        self.play_btn.draw(surface)
        self.settings_btn.draw(surface)
        self.quit_btn.draw(surface)

        ver = self.subtitle_font.render("v2.1 | Deluxe Pygame", True, DARK_GRAY)
        surface.blit(ver, (WINDOW_WIDTH // 2 - ver.get_width() // 2, WINDOW_HEIGHT - 40))


class SettingsMenu:
    """Меню настроек с возможностью переключения языка и сохранности в config.json"""

    def __init__(self):
        self.title_font = pygame.font.Font(None, 50)
        self.info_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)

        center_x = WINDOW_WIDTH // 2
        btn_w = 280

        self.lang_btn = Button(center_x - btn_w // 2, 190, btn_w, 40,
                               f"{t('language')}: {config_manager.language.upper()}",
                               BTN_BLUE, BTN_BLUE_HOVER, font_size=22)

        self.vol_btn = Button(center_x - btn_w // 2, 245, btn_w, 40,
                              f"{t('volume')}: {int(config_manager.volume * 100)}%",
                              BTN_BLUE, BTN_BLUE_HOVER, font_size=22)

        self.diff_btn = Button(center_x - btn_w // 2, 300, btn_w, 40,
                               f"{t('difficulty')}: {t(f'diff_{config_manager.difficulty}')}",
                               BTN_BLUE, BTN_BLUE_HOVER, font_size=22)

        self.back_btn = Button(center_x - btn_w // 2, 450, btn_w, 45,
                               t("back"), BTN_RED, BTN_RED_HOVER, font_size=26)

    def toggle_volume(self):
        config_manager.volume += 0.25
        if config_manager.volume > 1.05:
            config_manager.volume = 0.0
        sound_manager.set_volume(config_manager.volume)
        config_manager.save_config()

    def toggle_difficulty(self):
        config_manager.difficulty = (config_manager.difficulty + 1) % 3
        config_manager.save_config()

    def toggle_language(self):
        config_manager.toggle_language()

    def update(self, mouse_pos):
        self.lang_btn.text = f"{t('language')}: {config_manager.language.upper()}"
        self.vol_btn.text = f"{t('volume')}: {int(config_manager.volume * 100)}%"
        self.diff_btn.text = f"{t('difficulty')}: {t(f'diff_{config_manager.difficulty}')}"
        self.back_btn.text = t("back")

        self.lang_btn.update(mouse_pos)
        self.vol_btn.update(mouse_pos)
        self.diff_btn.update(mouse_pos)
        self.back_btn.update(mouse_pos)

    def draw(self, surface):
        surface.fill((15, 15, 25))

        title = self.title_font.render(t("settings"), True, WHITE)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 80))

        pygame.draw.line(surface, UI_BORDER,
                         (WINDOW_WIDTH // 2 - 150, 130),
                         (WINDOW_WIDTH // 2 + 150, 130), 2)

        self.lang_btn.draw(surface)
        self.vol_btn.draw(surface)
        self.diff_btn.draw(surface)

        controls_title = self.info_font.render(t("controls"), True, LIGHT_GRAY)
        surface.blit(controls_title, (WINDOW_WIDTH // 2 - controls_title.get_width() // 2, 355))

        controls = [
            t("controls_1"),
            t("controls_2"),
            t("controls_3"),
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
                                 t("resume"), BTN_GREEN, BTN_GREEN_HOVER, font_size=26)
        self.menu_btn = Button(center_x - btn_w // 2, 380, btn_w, 45,
                               t("menu"), BTN_RED, BTN_RED_HOVER, font_size=26)

    def update(self, mouse_pos):
        self.resume_btn.text = t("resume")
        self.menu_btn.text = t("menu")
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

        title = self.title_font.render(t("pause"), True, WHITE)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, box_y + 30))

        hint = self.info_font.render("ESC - " + t("resume").lower(), True, GRAY)
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
                               t("menu"), BTN_BLUE, BTN_BLUE_HOVER, font_size=26)

    def update(self, mouse_pos):
        self.menu_btn.text = t("menu")
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
            title_text = t("victory")
            title_color = (50, 255, 100)
        else:
            title_text = t("defeat")
            title_color = (255, 80, 80)

        pulse = math.sin(self.timer * 0.08) * 10
        title = self.title_font.render(title_text, True, title_color)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, box_y + 30 + int(pulse * 0.3)))

        stats = [
            f"{t('wave')}: {wave_reached}/{MAX_WAVES}",
            f"{t('kills')}: {kills}",
        ]

        for i, stat in enumerate(stats):
            stat_surf = self.info_font.render(stat, True, WHITE)
            surface.blit(stat_surf, (WINDOW_WIDTH // 2 - stat_surf.get_width() // 2, box_y + 120 + i * 35))

        if won:
            congrats = self.info_font.render(t("you_defended"), True, GOLD_COLOR)
            surface.blit(congrats, (WINDOW_WIDTH // 2 - congrats.get_width() // 2, box_y + 220))
        else:
            tip = self.info_font.render(t("try_again"), True, GRAY)
            surface.blit(tip, (WINDOW_WIDTH // 2 - tip.get_width() // 2, box_y + 220))

        self.menu_btn.draw(surface)