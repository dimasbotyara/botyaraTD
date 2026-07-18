# enemy.py — Все типы врагов

import pygame
import math
import random
from settings import *


class Enemy:
    """Базовый класс врага"""

    def __init__(self, enemy_type, path, wave_num=1):
        self.enemy_type = enemy_type
        self.path = path
        self.path_index = 0

        stats = ENEMY_STATS[enemy_type]
        self.name = stats["name"]

        # Масштабирование по волне
        scale = 1 + (wave_num - 1) * 0.12
        self.max_hp = stats["hp"] * scale
        self.hp = self.max_hp
        self.base_speed = stats["speed"]
        self.speed = self.base_speed
        self.reward = stats["reward"]

        # Позиция
        self.x = float(path[0][0])
        self.y = float(path[0][1])

        # Размер отображения
        self.radius = 10
        if enemy_type == "tank":
            self.radius = 14
        elif enemy_type == "boss":
            self.radius = 18
        elif enemy_type == "mega_boss":
            self.radius = 22
        elif enemy_type == "swarm":
            self.radius = 7
        elif enemy_type == "fast":
            self.radius = 8

        # Цвет
        self.color = ENEMY_COLORS.get(enemy_type, (200, 200, 200))

        # Статусные эффекты
        self.slow_timer = 0
        self.slow_amount = 0
        self.poison_timer = 0
        self.poison_dps = 0
        self.is_frozen_visual = False
        self.is_poisoned_visual = False

        # Щит (для shield типа)
        self.shield_hp = 0
        self.max_shield_hp = 0
        if enemy_type == "shield":
            self.shield_hp = stats.get("shield_hp", 80) * scale
            self.max_shield_hp = self.shield_hp

        # Хилер
        self.heal_range = stats.get("heal_range", 0)
        self.heal_amount = stats.get("heal_amount", 0)
        self.heal_cooldown = 0

        # Призрак
        self.stealth_chance = stats.get("stealth_chance", 0)
        self.is_stealthed = False
        self.stealth_timer = 0

        # Делитель
        self.can_split = enemy_type == "split"
        self.split_into = stats.get("split_into", 2)
        self.has_split = False

        # Состояние
        self.alive = True
        self.reached_end = False

        # Анимация
        self.anim_timer = random.randint(0, 100)
        self.angle = 0
        self.flash_timer = 0

    def apply_slow(self, amount, duration):
        """Замедление"""
        if amount > self.slow_amount:
            self.slow_amount = amount
            self.slow_timer = duration

    def apply_poison(self, dps, duration):
        """Отравление"""
        self.poison_dps = dps
        self.poison_timer = duration

    def take_damage(self, damage):
        """Получить урон"""
        self.flash_timer = 6

        # Призрак может уклониться
        if self.stealth_chance > 0 and random.random() < self.stealth_chance:
            return 0

        # Сначала щит
        if self.shield_hp > 0:
            if damage <= self.shield_hp:
                self.shield_hp -= damage
                return damage
            else:
                damage -= self.shield_hp
                self.shield_hp = 0

        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return damage

    def update(self, enemies_list=None):
        """Обновление позиции и эффектов"""
        if not self.alive:
            return

        self.anim_timer += 1

        # Замедление
        if self.slow_timer > 0:
            self.slow_timer -= 1
            self.speed = self.base_speed * (1 - self.slow_amount)
            self.is_frozen_visual = True
        else:
            self.speed = self.base_speed
            self.slow_amount = 0
            self.is_frozen_visual = False

        # Яд
        if self.poison_timer > 0:
            self.poison_timer -= 1
            self.hp -= self.poison_dps / 60  # урон в секунду -> урон в кадр
            self.is_poisoned_visual = True
            if self.hp <= 0:
                self.hp = 0
                self.alive = False
        else:
            self.poison_dps = 0
            self.is_poisoned_visual = False

        # Призрак - стелс
        if self.stealth_chance > 0:
            self.stealth_timer += 1
            if self.stealth_timer % 120 == 0:
                self.is_stealthed = not self.is_stealthed

        # Хилер - лечит ближайших
        if self.heal_range > 0 and enemies_list and self.heal_cooldown <= 0:
            self.heal_cooldown = 30
            for other in enemies_list:
                if other is self or not other.alive:
                    continue
                dist = math.hypot(other.x - self.x, other.y - self.y)
                if dist < self.heal_range:
                    heal = other.max_hp * self.heal_amount / 60
                    other.hp = min(other.max_hp, other.hp + heal)
        if self.heal_cooldown > 0:
            self.heal_cooldown -= 1

        # Движение по пути
        if self.path_index < len(self.path) - 1:
            target = self.path[self.path_index + 1]
            dx = target[0] - self.x
            dy = target[1] - self.y
            dist = math.hypot(dx, dy)

            if dist > 0:
                self.angle = math.atan2(dy, dx)

            if dist < self.speed:
                self.path_index += 1
                if self.path_index >= len(self.path) - 1:
                    self.reached_end = True
                    self.alive = False
            else:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed

    def get_split_enemies(self):
        """Создает мелких врагов при смерти делителя"""
        if not self.can_split or self.has_split:
            return []
        self.has_split = True
        new_enemies = []
        for i in range(self.split_into):
            child = Enemy("swarm", self.path)
            child.path_index = self.path_index
            child.x = self.x + random.uniform(-10, 10)
            child.y = self.y + random.uniform(-10, 10)
            child.max_hp = self.max_hp * 0.3
            child.hp = child.max_hp
            child.speed = self.base_speed * 1.5
            child.base_speed = child.speed
            child.reward = self.reward // 3
            new_enemies.append(child)
        return new_enemies

    def draw(self, surface):
        """Отрисовка врага"""
        if not self.alive:
            return

        x, y = int(self.x), int(self.y)
        r = self.radius

        # Тень
        shadow_surf = pygame.Surface((r * 2 + 4, r + 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 50), (0, 0, r * 2 + 4, r + 2))
        surface.blit(shadow_surf, (x - r - 2, y + r // 2))

        # Основной цвет
        color = self.color

        # Мигание при уроне
        if self.flash_timer > 0:
            self.flash_timer -= 1
            color = (255, 255, 255)

        # Стелс
        if self.is_stealthed:
            alpha = 80 + int(40 * math.sin(self.anim_timer * 0.1))
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (r + 1, r + 1), r)
            surface.blit(s, (x - r - 1, y - r - 1))
        else:
            # Тело
            if self.enemy_type in ("tank", "boss", "mega_boss"):
                # Квадратные враги (танки/боссы)
                rect = pygame.Rect(x - r, y - r, r * 2, r * 2)
                pygame.draw.rect(surface, color, rect, border_radius=4)
                darker = (max(0, color[0] - 40), max(0, color[1] - 40), max(0, color[2] - 40))
                pygame.draw.rect(surface, darker, rect, 2, border_radius=4)
                # Внутренний рисунок
                inner_r = r // 2
                pygame.draw.rect(surface, darker, (x - inner_r, y - inner_r, inner_r * 2, inner_r * 2), border_radius=2)
            elif self.enemy_type == "fast":
                # Треугольник для быстрых
                cos_a = math.cos(self.angle)
                sin_a = math.sin(self.angle)
                p1 = (x + cos_a * r * 1.3, y + sin_a * r * 1.3)
                p2 = (x + math.cos(self.angle + 2.5) * r, y + math.sin(self.angle + 2.5) * r)
                p3 = (x + math.cos(self.angle - 2.5) * r, y + math.sin(self.angle - 2.5) * r)
                pygame.draw.polygon(surface, color, [p1, p2, p3])
                darker = (max(0, color[0] - 50), max(0, color[1] - 50), max(0, color[2] - 50))
                pygame.draw.polygon(surface, darker, [p1, p2, p3], 2)
            elif self.enemy_type == "healer":
                # Крестик для хилера
                pygame.draw.circle(surface, color, (x, y), r)
                pygame.draw.rect(surface, (255, 255, 255), (x - 2, y - r // 2, 4, r))
                pygame.draw.rect(surface, (255, 255, 255), (x - r // 2, y - 2, r, 4))
            elif self.enemy_type == "ghost":
                # Волнистый для призрака
                pygame.draw.circle(surface, color, (x, y - 2), r)
                wave_y = y + r // 2
                for wx in range(-r, r + 1, 4):
                    wy = int(math.sin((wx + self.anim_timer * 3) * 0.3) * 3)
                    pygame.draw.circle(surface, color, (x + wx, wave_y + wy), 3)
            else:
                # Круглые враги (остальные)
                pygame.draw.circle(surface, color, (x, y), r)
                darker = (max(0, color[0] - 50), max(0, color[1] - 50), max(0, color[2] - 50))
                pygame.draw.circle(surface, darker, (x, y), r, 2)
                # Блик
                highlight = (min(255, color[0] + 60), min(255, color[1] + 60), min(255, color[2] + 60))
                pygame.draw.circle(surface, highlight, (x - r // 3, y - r // 3), r // 3)

        # Щит
        if self.shield_hp > 0:
            shield_ratio = self.shield_hp / self.max_shield_hp
            shield_color = (100, 150, 255, int(120 * shield_ratio))
            shield_surf = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, shield_color, (r + 4, r + 4), r + 3, 2)
            surface.blit(shield_surf, (x - r - 4, y - r - 4))

        # Эффект заморозки
        if self.is_frozen_visual:
            frost_surf = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
            pygame.draw.circle(frost_surf, (150, 220, 255, 60), (r + 3, r + 3), r + 2)
            surface.blit(frost_surf, (x - r - 3, y - r - 3))

        # Эффект яда
        if self.is_poisoned_visual:
            poison_surf = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
            pygame.draw.circle(poison_surf, (80, 200, 50, 50), (r + 3, r + 3), r + 2)
            surface.blit(poison_surf, (x - r - 3, y - r - 3))

        # Хилер - кольцо лечения
        if self.heal_range > 0:
            heal_alpha = int(30 + 15 * math.sin(self.anim_timer * 0.05))
            heal_surf = pygame.Surface((self.heal_range * 2 + 4, self.heal_range * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(heal_surf, (255, 150, 200, heal_alpha),
                               (self.heal_range + 2, self.heal_range + 2), self.heal_range, 1)
            surface.blit(heal_surf, (x - self.heal_range - 2, y - self.heal_range - 2))

        # HP бар
        self._draw_hp_bar(surface, x, y, r)

    def _draw_hp_bar(self, surface, x, y, r):
        """Полоска здоровья"""
        bar_width = r * 2 + 4
        bar_height = 4
        bar_x = x - bar_width // 2
        bar_y = y - r - 8

        # Фон
        pygame.draw.rect(surface, HP_BG, (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2), border_radius=2)

        # HP
        hp_ratio = self.hp / self.max_hp
        if hp_ratio > 0.6:
            hp_color = HP_GREEN
        elif hp_ratio > 0.3:
            hp_color = HP_YELLOW
        else:
            hp_color = HP_RED

        fill_width = int(bar_width * hp_ratio)
        if fill_width > 0:
            pygame.draw.rect(surface, hp_color, (bar_x, bar_y, fill_width, bar_height), border_radius=2)

        # Щит бар
        if self.max_shield_hp > 0 and self.shield_hp > 0:
            shield_ratio = self.shield_hp / self.max_shield_hp
            shield_width = int(bar_width * shield_ratio)
            pygame.draw.rect(surface, (100, 150, 255), (bar_x, bar_y - 5, shield_width, 3), border_radius=1)