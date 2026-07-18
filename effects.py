# effects.py — Частицы, взрывы, визуальные эффекты

import pygame
import random
import math


class Particle:
    """Одна частица"""
    def __init__(self, x, y, color, vel_x, vel_y, size, lifetime, gravity=0.05, shrink=True):
        self.x = x
        self.y = y
        self.color = color
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.size = size
        self.max_lifetime = lifetime
        self.lifetime = lifetime
        self.gravity = gravity
        self.shrink = shrink
        self.alive = True

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += self.gravity
        self.vel_x *= 0.98
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        alpha_ratio = self.lifetime / self.max_lifetime
        current_size = self.size * alpha_ratio if self.shrink else self.size
        if current_size < 0.5:
            return
        r = min(255, int(self.color[0] * alpha_ratio + 50 * (1 - alpha_ratio)))
        g = min(255, int(self.color[1] * alpha_ratio))
        b = min(255, int(self.color[2] * alpha_ratio))
        pygame.draw.circle(surface, (r, g, b), (int(self.x), int(self.y)), max(1, int(current_size)))


class FloatingText:
    """Всплывающий текст (урон, золото и т.д.)"""
    def __init__(self, x, y, text, color, size=20, lifetime=45):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.font = pygame.font.Font(None, size)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True

    def update(self):
        self.y -= 0.8
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        alpha_ratio = self.lifetime / self.max_lifetime
        r = int(self.color[0] * alpha_ratio)
        g = int(self.color[1] * alpha_ratio)
        b = int(self.color[2] * alpha_ratio)
        text_surf = self.font.render(self.text, True, (r, g, b))
        surface.blit(text_surf, (int(self.x) - text_surf.get_width() // 2, int(self.y)))


class LaserBeam:
    """Лазерный луч (для лазерной башни)"""
    def __init__(self, start, end, color=(255, 50, 50), width=3, lifetime=8):
        self.start = start
        self.end = end
        self.color = color
        self.width = width
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        alpha_ratio = self.lifetime / self.max_lifetime
        w = max(1, int(self.width * alpha_ratio))
        r = int(self.color[0] * alpha_ratio)
        g = int(self.color[1] * alpha_ratio)
        b = int(self.color[2] * alpha_ratio)
        pygame.draw.line(surface, (r, g, b), self.start, self.end, w)
        # Glow эффект
        if w > 1:
            glow_color = (min(255, r + 50), min(255, g + 50), min(255, b + 50))
            pygame.draw.line(surface, glow_color, self.start, self.end, max(1, w - 1))


class LightningBolt:
    """Молния (для теслы)"""
    def __init__(self, start, end, color=(180, 130, 255), lifetime=12, segments=8):
        self.start = start
        self.end = end
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True
        self.points = self._generate_points(segments)

    def _generate_points(self, segments):
        points = [self.start]
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        for i in range(1, segments):
            t = i / segments
            x = self.start[0] + dx * t + random.uniform(-15, 15)
            y = self.start[1] + dy * t + random.uniform(-15, 15)
            points.append((x, y))
        points.append(self.end)
        return points

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive or len(self.points) < 2:
            return
        alpha_ratio = self.lifetime / self.max_lifetime
        r = int(self.color[0] * alpha_ratio)
        g = int(self.color[1] * alpha_ratio)
        b = int(self.color[2] * alpha_ratio)
        color = (min(255, r), min(255, g), min(255, b))
        pygame.draw.lines(surface, color, False, [(int(p[0]), int(p[1])) for p in self.points], 2)
        # Яркий центр
        bright = (min(255, r + 80), min(255, g + 80), min(255, b + 80))
        pygame.draw.lines(surface, bright, False, [(int(p[0]), int(p[1])) for p in self.points], 1)


class EffectsManager:
    """Управление всеми эффектами"""
    def __init__(self):
        self.particles = []
        self.floating_texts = []
        self.beams = []
        self.lightnings = []

    def add_explosion(self, x, y, color, count=12, speed=3, size=4, lifetime=30):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(0.5, speed)
            vel_x = math.cos(angle) * spd
            vel_y = math.sin(angle) * spd
            s = random.uniform(size * 0.5, size * 1.5)
            lt = random.randint(int(lifetime * 0.5), lifetime)
            r = min(255, color[0] + random.randint(-30, 30))
            g = min(255, color[1] + random.randint(-30, 30))
            b = min(255, color[2] + random.randint(-30, 30))
            r = max(0, r)
            g = max(0, g)
            b = max(0, b)
            self.particles.append(Particle(x, y, (r, g, b), vel_x, vel_y, s, lt))

    def add_death_explosion(self, x, y, color):
        self.add_explosion(x, y, color, count=20, speed=4, size=5, lifetime=35)
        # Кольцо
        for i in range(12):
            angle = (2 * math.pi / 12) * i
            vel_x = math.cos(angle) * 2.5
            vel_y = math.sin(angle) * 2.5
            self.particles.append(Particle(x, y, (255, 255, 200), vel_x, vel_y, 3, 20))

    def add_hit_effect(self, x, y, color):
        self.add_explosion(x, y, color, count=5, speed=1.5, size=2.5, lifetime=15)

    def add_floating_text(self, x, y, text, color, size=20, lifetime=45):
        self.floating_texts.append(FloatingText(x, y, text, color, size, lifetime))

    def add_gold_text(self, x, y, amount):
        self.floating_texts.append(FloatingText(x, y, f"+{amount}g", (255, 215, 0), 22, 50))

    def add_damage_text(self, x, y, damage):
        self.floating_texts.append(FloatingText(x, y, f"-{int(damage)}", (255, 80, 80), 18, 30))

    def add_laser_beam(self, start, end, color=(255, 50, 50)):
        self.beams.append(LaserBeam(start, end, color))

    def add_lightning(self, start, end, color=(180, 130, 255)):
        self.lightnings.append(LightningBolt(start, end, color))

    def add_freeze_effect(self, x, y):
        for _ in range(6):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(0.3, 1.5)
            self.particles.append(
                Particle(x, y, (150, 220, 255), math.cos(angle) * spd, math.sin(angle) * spd - 0.5,
                         random.uniform(2, 4), random.randint(20, 40), gravity=0.01)
            )

    def add_poison_effect(self, x, y):
        for _ in range(4):
            ox = random.uniform(-8, 8)
            oy = random.uniform(-8, 8)
            self.particles.append(
                Particle(x + ox, y + oy, (100, 220, 60), random.uniform(-0.3, 0.3), random.uniform(-1, -0.3),
                         random.uniform(2, 3.5), random.randint(20, 35), gravity=-0.02)
            )

    def add_splash_ring(self, x, y, radius, color):
        """Кольцо для AOE-эффекта"""
        segments = 20
        for i in range(segments):
            angle = (2 * math.pi / segments) * i
            px = x + math.cos(angle) * radius
            py = y + math.sin(angle) * radius
            self.particles.append(
                Particle(px, py, color, math.cos(angle) * 0.5, math.sin(angle) * 0.5,
                         2.5, 20, gravity=0)
            )

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

        for t in self.floating_texts:
            t.update()
        self.floating_texts = [t for t in self.floating_texts if t.alive]

        for b in self.beams:
            b.update()
        self.beams = [b for b in self.beams if b.alive]

        for l in self.lightnings:
            l.update()
        self.lightnings = [l for l in self.lightnings if l.alive]

    def draw(self, surface):
        for b in self.beams:
            b.draw(surface)
        for l in self.lightnings:
            l.draw(surface)
        for p in self.particles:
            p.draw(surface)
        for t in self.floating_texts:
            t.draw(surface)