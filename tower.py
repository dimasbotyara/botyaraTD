# tower.py — Все типы башен с отдачей и звуковыми эффектами

import pygame
import math
from settings import *
from projectile import Projectile
from sound import sound_manager


class Tower:
    """Базовый класс башни"""

    def __init__(self, col, row, tower_type):
        self.col = col
        self.row = row
        self.tower_type = tower_type
        self.level = 0  # 0, 1, 2 (три уровня)

        # Позиция центра в пикселях
        self.x = col * CELL_SIZE + CELL_SIZE // 2
        self.y = row * CELL_SIZE + CELL_SIZE // 2

        # Загрузка статов
        self.stats_data = TOWER_STATS[tower_type]
        self.name = self.stats_data["name"]
        self.desc = self.stats_data["desc"]
        self._load_stats()

        # Таймер стрельбы
        self.fire_cooldown = 0
        self.target = None

        # Цвет
        self.color = TOWER_COLORS[tower_type]
        self.color_dark = TOWER_COLORS_DARK[tower_type]

        # Потраченное золото (для продажи)
        self.total_spent = self.stats_data["levels"][0]["cost"]

        # Анимация и отдача
        self.anim_angle = 0  # Угол поворота ствола
        self.shoot_flash = 0
        self.pulse_timer = 0
        self.recoil = 0.0  # Смещение от отдачи при выстреле

        # Специальные башни
        self.laser_target = None
        self.is_laser = tower_type == "laser"
        self.is_tesla = tower_type == "tesla"

    def _load_stats(self):
        """Загрузить статы текущего уровня"""
        level_data = self.stats_data["levels"][self.level]
        self.damage = level_data["damage"]
        self.fire_rate = level_data["fire_rate"]
        self.range = level_data["range"]

        # Специальные свойства
        self.slow_amount = level_data.get("slow", 0)
        self.slow_duration = level_data.get("slow_duration", 0)
        self.splash_radius = level_data.get("splash", 0)
        self.dot_damage = level_data.get("dot", 0)
        self.dot_duration = level_data.get("dot_duration", 0)
        self.chain_count = level_data.get("chain", 0)

    def get_upgrade_cost(self):
        """Цена улучшения"""
        if self.level >= 2:
            return None
        return self.stats_data["levels"][self.level + 1]["cost"]

    def upgrade(self):
        """Улучшить башню"""
        if self.level >= 2:
            return False
        cost = self.get_upgrade_cost()
        self.level += 1
        self.total_spent += cost
        self._load_stats()
        sound_manager.play("gold")
        return True

    def get_sell_price(self):
        """Цена продажи"""
        return int(self.total_spent * SELL_RATIO)

    def find_target(self, enemies):
        """Найти ближайшего врага в радиусе"""
        best_target = None
        best_progress = -1

        for enemy in enemies:
            if not enemy.alive:
                continue
            dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if dist <= self.range:
                if enemy.path_index > best_progress:
                    best_progress = enemy.path_index
                    best_target = enemy

        return best_target

    def update(self, enemies, projectiles, effects_manager):
        """Обновление башни"""
        self.pulse_timer += 1

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

        if self.shoot_flash > 0:
            self.shoot_flash -= 1

        # Демпфирование отдачи
        if self.recoil > 0:
            self.recoil = max(0.0, self.recoil - 0.8)

        # Найти цель
        self.target = self.find_target(enemies)

        if self.target:
            # Повернуть ствол к цели
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            self.anim_angle = math.atan2(dy, dx)

            # Стрелять
            if self.fire_cooldown <= 0:
                self.fire_cooldown = self.fire_rate
                self.shoot(self.target, enemies, projectiles, effects_manager)
                self.shoot_flash = 8
                self.recoil = 6.0  # Импульс отдачи ствола!
                sound_manager.play(self.tower_type)
        else:
            self.laser_target = None

        # Лазер - постоянный урон
        if self.is_laser and self.target:
            self.laser_target = self.target
            self.target.take_damage(self.damage)
            if self.slow_amount > 0:
                self.target.apply_slow(self.slow_amount, 10)

    def shoot(self, target, enemies, projectiles, effects_manager):
        """Выстрел"""
        if self.is_laser:
            effects_manager.add_laser_beam(
                (self.x, self.y),
                (target.x, target.y),
                (255, 50, 50)
            )
            return

        if self.is_tesla:
            self._tesla_attack(target, enemies, effects_manager)
            return

        # Снаряд
        proj_type = "bullet"
        color = (255, 255, 200)
        speed = 7
        size = 3

        if self.tower_type == "sniper":
            proj_type = "sniper_bullet"
            color = (100, 150, 255)
            speed = 15
            size = 2
        elif self.tower_type == "freeze":
            proj_type = "freeze_bullet"
            color = (150, 220, 255)
            speed = 6
            size = 4
        elif self.tower_type == "cannon":
            proj_type = "cannonball"
            color = (200, 140, 50)
            speed = 5
            size = 5
        elif self.tower_type == "poison":
            proj_type = "poison_bullet"
            color = (80, 200, 80)
            speed = 5
            size = 4
        elif self.tower_type == "missile":
            proj_type = "missile"
            color = (220, 220, 80)
            speed = 4
            size = 4

        barrel_len = CELL_SIZE // 2 + 4
        start_x = self.x + math.cos(self.anim_angle) * (barrel_len - self.recoil)
        start_y = self.y + math.sin(self.anim_angle) * (barrel_len - self.recoil)

        proj = Projectile(start_x, start_y, target, self.damage, speed, color, size, proj_type)
        proj.splash_radius = self.splash_radius
        proj.slow_amount = self.slow_amount
        proj.slow_duration = self.slow_duration
        proj.dot_damage = self.dot_damage
        proj.dot_duration = self.dot_duration

        projectiles.append(proj)

    def _tesla_attack(self, target, enemies, effects_manager):
        """Атака теслы - молния по цепи"""
        hit_enemies = [target]
        target.take_damage(self.damage)
        effects_manager.add_lightning((self.x, self.y), (target.x, target.y))

        current = target
        remaining_chains = self.chain_count - 1
        chain_damage = self.damage

        while remaining_chains > 0:
            chain_damage *= 0.7
            best = None
            best_dist = 100

            for enemy in enemies:
                if not enemy.alive or enemy in hit_enemies:
                    continue
                dist = math.hypot(enemy.x - current.x, enemy.y - current.y)
                if dist < best_dist:
                    best_dist = dist
                    best = enemy

            if best:
                best.take_damage(chain_damage)
                effects_manager.add_lightning((current.x, current.y), (best.x, best.y))
                hit_enemies.append(best)
                current = best
                remaining_chains -= 1
            else:
                break

    def draw(self, surface, selected=False, hover=False):
        """Отрисовка башни с учетом отдачи ствола"""
        x, y = self.x, self.y
        half = CELL_SIZE // 2

        # Подсветка при наведении/выделении
        if selected:
            range_surf = pygame.Surface((self.range * 2 + 4, self.range * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(range_surf, (255, 255, 255, 25), (self.range + 2, self.range + 2), self.range)
            pygame.draw.circle(range_surf, (255, 255, 255, 50), (self.range + 2, self.range + 2), self.range, 1)
            surface.blit(range_surf, (x - self.range - 2, y - self.range - 2))

        if hover:
            hs = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(hs, (255, 255, 255, 30), (0, 0, CELL_SIZE, CELL_SIZE))
            surface.blit(hs, (self.col * CELL_SIZE, self.row * CELL_SIZE))

        # База башни
        base_rect = pygame.Rect(x - half + 3, y - half + 3, CELL_SIZE - 6, CELL_SIZE - 6)
        pygame.draw.rect(surface, self.color_dark, base_rect, border_radius=5)

        inner_rect = pygame.Rect(x - half + 5, y - half + 5, CELL_SIZE - 10, CELL_SIZE - 10)
        pygame.draw.rect(surface, self.color, inner_rect, border_radius=4)

        # Уровень - звёздочки
        for i in range(self.level + 1):
            star_x = x - (self.level * 4) + i * 8
            star_y = y + half - 5
            pygame.draw.circle(surface, GOLD_COLOR, (star_x, star_y), 2)

        # Длина ствола с эффектом отдачи!
        barrel_len = half + 2 - self.recoil
        cos_a = math.cos(self.anim_angle)
        sin_a = math.sin(self.anim_angle)

        if self.tower_type == "machinegun":
            for offset in (-3, 3):
                perp_x = -sin_a * offset
                perp_y = cos_a * offset
                start = (x + perp_x, y + perp_y)
                end = (x + cos_a * barrel_len + perp_x, y + sin_a * barrel_len + perp_y)
                pygame.draw.line(surface, (80, 80, 90), (int(start[0]), int(start[1])),
                                 (int(end[0]), int(end[1])), 3)

        elif self.tower_type == "sniper":
            end = (x + cos_a * (barrel_len + 6), y + sin_a * (barrel_len + 6))
            pygame.draw.line(surface, (40, 40, 120), (int(x), int(y)), (int(end[0]), int(end[1])), 4)
            pygame.draw.circle(surface, (80, 80, 200), (int(end[0]), int(end[1])), 3)

        elif self.tower_type == "freeze":
            crystal_pulse = math.sin(self.pulse_timer * 0.08) * 2
            cr = int(6 + crystal_pulse)
            pygame.draw.polygon(surface, (150, 220, 255), [
                (x, y - cr), (x + cr, y), (x, y + cr), (x - cr, y)
            ])
            pygame.draw.polygon(surface, (200, 240, 255), [
                (x, y - cr), (x + cr, y), (x, y + cr), (x - cr, y)
            ], 1)

        elif self.tower_type == "cannon":
            end = (x + cos_a * barrel_len, y + sin_a * barrel_len)
            pygame.draw.line(surface, (150, 60, 20), (int(x), int(y)), (int(end[0]), int(end[1])), 6)
            pygame.draw.circle(surface, (180, 80, 30), (int(end[0]), int(end[1])), 4)

        elif self.tower_type == "laser":
            pulse = math.sin(self.pulse_timer * 0.1) * 2
            end = (x + cos_a * barrel_len, y + sin_a * barrel_len)
            pygame.draw.line(surface, (200, 30, 30), (int(x), int(y)), (int(end[0]), int(end[1])), 3)
            pygame.draw.circle(surface, (255, 80 + int(pulse * 10), 80), (int(end[0]), int(end[1])), int(4 + pulse))
            if self.laser_target and self.target and self.target.alive:
                beam_surf = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(beam_surf, (255, 50, 50, 150),
                                 (int(end[0]), int(end[1])),
                                 (int(self.target.x), int(self.target.y)), 2)
                pygame.draw.line(beam_surf, (255, 100, 100, 50),
                                 (int(end[0]), int(end[1])),
                                 (int(self.target.x), int(self.target.y)), 5)
                surface.blit(beam_surf, (0, 0))

        elif self.tower_type == "poison":
            pygame.draw.circle(surface, (50, 150, 50), (x, y), 8)
            pygame.draw.circle(surface, (80, 220, 80), (x, y), 5)
            bx = x + int(math.sin(self.pulse_timer * 0.15) * 5)
            by = y - 8 - int(abs(math.sin(self.pulse_timer * 0.1)) * 4)
            pygame.draw.circle(surface, (100, 230, 100), (bx, by), 2)

        elif self.tower_type == "tesla":
            coil_height = 12 + int(math.sin(self.pulse_timer * 0.12) * 2)
            pygame.draw.line(surface, (140, 100, 220), (x, y + 4), (x, y - coil_height), 3)
            pygame.draw.circle(surface, (200, 160, 255), (x, y - coil_height), 5)
            pygame.draw.circle(surface, (220, 200, 255), (x, y - coil_height), 3)

        elif self.tower_type == "missile":
            for angle_off in (-0.3, 0, 0.3):
                a = self.anim_angle + angle_off
                end = (x + math.cos(a) * barrel_len, y + math.sin(a) * barrel_len)
                pygame.draw.line(surface, (160, 160, 40), (int(x), int(y)), (int(end[0]), int(end[1])), 3)

        # Вспышка выстрела
        if self.shoot_flash > 0:
            flash_size = self.shoot_flash
            flash_surf = pygame.Surface((flash_size * 4, flash_size * 4), pygame.SRCALPHA)
            fx = x + cos_a * barrel_len
            fy = y + sin_a * barrel_len
            pygame.draw.circle(flash_surf, (255, 255, 150, int(180 * (self.shoot_flash / 8))),
                               (flash_size * 2, flash_size * 2), flash_size * 2)
            surface.blit(flash_surf, (int(fx) - flash_size * 2, int(fy) - flash_size * 2))