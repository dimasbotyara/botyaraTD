# projectile.py — Снаряды башен

import pygame
import math
import random


class Projectile:
    """Базовый снаряд"""

    def __init__(self, x, y, target, damage, speed=6, color=(255, 255, 200),
                 size=3, proj_type="bullet"):
        self.x = float(x)
        self.y = float(y)
        self.target = target
        self.damage = damage
        self.speed = speed
        self.color = color
        self.size = size
        self.proj_type = proj_type
        self.alive = True

        # Для ракет
        self.trail = []
        self.max_trail = 8

        # Splash (AOE)
        self.splash_radius = 0

        # Slow
        self.slow_amount = 0
        self.slow_duration = 0

        # Poison
        self.dot_damage = 0
        self.dot_duration = 0

    def update(self):
        """Движение к цели"""
        if not self.alive:
            return

        if self.target is None or not self.target.alive:
            self.alive = False
            return

        # Сохраняем позицию для трейла
        if self.proj_type == "missile":
            self.trail.append((self.x, self.y))
            if len(self.trail) > self.max_trail:
                self.trail.pop(0)

        # Направление к цели
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)

        if dist < self.speed + self.target.radius:
            # Попадание!
            self.hit()
            return

        # Ракеты имеют плавный поворот
        if self.proj_type == "missile":
            # Самонаведение с инерцией
            angle = math.atan2(dy, dx)
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed
        else:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

    def hit(self):
        """Попадание по цели"""
        self.alive = False
        if self.target and self.target.alive:
            self.target.take_damage(self.damage)

            # Замедление
            if self.slow_amount > 0:
                self.target.apply_slow(self.slow_amount, self.slow_duration)

            # Яд
            if self.dot_damage > 0:
                self.target.apply_poison(self.dot_damage, self.dot_duration)

    def draw(self, surface):
        """Отрисовка"""
        if not self.alive:
            return

        x, y = int(self.x), int(self.y)

        if self.proj_type == "bullet":
            # Обычная пуля
            pygame.draw.circle(surface, self.color, (x, y), self.size)
            # Glow
            glow = pygame.Surface((self.size * 4, self.size * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*self.color, 60), (self.size * 2, self.size * 2), self.size * 2)
            surface.blit(glow, (x - self.size * 2, y - self.size * 2))

        elif self.proj_type == "sniper_bullet":
            # Снайперская пуля - длинная
            if self.target and self.target.alive:
                angle = math.atan2(self.target.y - self.y, self.target.x - self.x)
            else:
                angle = 0
            end_x = x + math.cos(angle) * 8
            end_y = y + math.sin(angle) * 8
            pygame.draw.line(surface, self.color, (x, y), (int(end_x), int(end_y)), 2)
            pygame.draw.circle(surface, (255, 255, 255), (x, y), 2)

        elif self.proj_type == "freeze_bullet":
            # Ледяная пуля
            pygame.draw.circle(surface, (150, 220, 255), (x, y), self.size + 1)
            pygame.draw.circle(surface, (200, 240, 255), (x, y), self.size)
            # Снежинки
            for angle_off in range(0, 360, 60):
                angle = math.radians(angle_off + self.x * 3)
                px = x + math.cos(angle) * (self.size + 3)
                py = y + math.sin(angle) * (self.size + 3)
                pygame.draw.circle(surface, (200, 240, 255), (int(px), int(py)), 1)

        elif self.proj_type == "cannonball":
            # Ядро пушки
            pygame.draw.circle(surface, (60, 60, 60), (x, y), self.size + 2)
            pygame.draw.circle(surface, self.color, (x, y), self.size)
            pygame.draw.circle(surface, (200, 200, 200), (x - 1, y - 1), max(1, self.size // 2))

        elif self.proj_type == "poison_bullet":
            # Ядовитая капля
            pygame.draw.circle(surface, (60, 180, 60), (x, y), self.size + 1)
            pygame.draw.circle(surface, (80, 220, 80), (x, y), self.size)
            # Капельки
            if random.random() > 0.5:
                drip_y = y + random.randint(2, 6)
                pygame.draw.circle(surface, (80, 200, 60), (x + random.randint(-3, 3), drip_y), 1)

        elif self.proj_type == "missile":
            # Ракета с трейлом
            # Трейл
            for i, pos in enumerate(self.trail):
                alpha = int((i / self.max_trail) * 150)
                trail_size = max(1, int((i / self.max_trail) * 3))
                trail_color = (255, 150 + int(100 * (i / max(1, self.max_trail))), 50)
                ts = pygame.Surface((trail_size * 2 + 2, trail_size * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(ts, (*trail_color, alpha), (trail_size + 1, trail_size + 1), trail_size)
                surface.blit(ts, (int(pos[0]) - trail_size - 1, int(pos[1]) - trail_size - 1))

            # Ракета
            if self.target and self.target.alive:
                angle = math.atan2(self.target.y - self.y, self.target.x - self.x)
            else:
                angle = 0
            # Тело ракеты
            tip_x = x + math.cos(angle) * 6
            tip_y = y + math.sin(angle) * 6
            left_x = x + math.cos(angle + 2.5) * 5
            left_y = y + math.sin(angle + 2.5) * 5
            right_x = x + math.cos(angle - 2.5) * 5
            right_y = y + math.sin(angle - 2.5) * 5
            pygame.draw.polygon(surface, self.color, [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)])
            pygame.draw.polygon(surface, (255, 255, 200), [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)], 1)