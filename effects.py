# effects.py — Частицы, взрывы, визуальные эффекты и тряска экрана

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


class ShockwaveRing:
    """Расширяющаяся ударная волна"""
    def __init__(self, x, y, max_radius=60, color=(255, 200, 100), width=4, speed=4):
        self.x = x
        self.y = y
        self.radius = 5
        self.max_radius = max_radius
        self.color = color
        self.width = width
        self.speed = speed
        self.alive = True

    def update(self):
        self.radius += self.speed
        if self.radius >= self.max_radius:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        progress = self.radius / self.max_radius
        alpha = int(255 * (1 - progress))
        current_width = max(1, int(self.width * (1 - progress)))
        
        s = pygame.Surface((self.radius * 2 + 10, self.radius * 2 + 10), pygame.SRCALPHA)
        center = (self.radius + 5, self.radius + 5)
        color_with_alpha = (self.color[0], self.color[1], self.color[2], alpha)
        pygame.draw.circle(s, color_with_alpha, center, int(self.radius), current_width)
        surface.blit(s, (int(self.x - self.radius - 5), int(self.y - self.radius - 5)))


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
        
        # Обводка текста для сочности
        text_shadow = self.font.render(self.text, True, (0, 0, 0))
        surface.blit(text_shadow, (int(self.x) - text_shadow.get_width() // 2 + 1, int(self.y) + 1))
        
        text_surf = self.font.render(self.text, True, (r, g, b))
        surface.blit(text_surf, (int(self.x) - text_surf.get_width() // 2, int(self.y)))


class LaserBeam:
    """Лазерный луч (для лазерной башни)"""
    def __init__(self, start, end, color=(255, 50, 50), width=4, lifetime=8):
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
        pygame.draw.line(surface, (r, g, b), self.start, self.end, w + 2)
        # Яркий белый центр
        glow_color = (255, 255, 255)
        pygame.draw.line(surface, glow_color, self.start, self.end, max(1, w))


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
        pygame.draw.lines(surface, color, False, [(int(p[0]), int(p[1])) for p in self.points], 3)
        # Яркий центр
        bright = (255, 255, 255)
        pygame.draw.lines(surface, bright, False, [(int(p[0]), int(p[1])) for p in self.points], 1)


class EffectsManager:
    """Управление всеми эффектами и тряской экрана"""
    def __init__(self):
        self.particles = []
        self.shockwaves = []
        self.floating_texts = []
        self.beams = []
        self.lightnings = []
        self.shake_amount = 0

    def add_shake(self, amount):
        """Добавить силу тряски экрана"""
        self.shake_amount = min(20.0, self.shake_amount + amount)

    def get_shake_offset(self):
        """Смещение камеры для отрисовки кадра"""
        if self.shake_amount > 0.5:
            ox = random.uniform(-self.shake_amount, self.shake_amount)
            oy = random.uniform(-self.shake_amount, self.shake_amount)
            return int(ox), int(oy)
        return 0, 0

    def add_explosion(self, x, y, color, count=14, speed=3.5, size=4, lifetime=30):
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
            self.particles.append(Particle(x, y, (max(0, r), max(0, g), max(0, b)), vel_x, vel_y, s, lt))

    def add_death_explosion(self, x, y, color):
        self.add_explosion(x, y, color, count=24, speed=4.5, size=5, lifetime=35)
        self.shockwaves.append(ShockwaveRing(x, y, max_radius=40, color=(255, 220, 100)))
        self.add_shake(2.0)

    def add_airstrike_explosion(self, x, y):
        self.add_explosion(x, y, (255, 100, 30), count=40, speed=6.0, size=7, lifetime=45)
        self.shockwaves.append(ShockwaveRing(x, y, max_radius=80, color=(255, 150, 50), width=6))
        self.add_shake(12.0)

    def add_hit_effect(self, x, y, color):
        self.add_explosion(x, y, color, count=6, speed=1.8, size=2.5, lifetime=15)

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
        self.add_shake(0.5)

    def add_freeze_effect(self, x, y):
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(0.3, 1.8)
            self.particles.append(
                Particle(x, y, (150, 220, 255), math.cos(angle) * spd, math.sin(angle) * spd - 0.5,
                         random.uniform(2, 4.5), random.randint(20, 40), gravity=0.01)
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
        self.shockwaves.append(ShockwaveRing(x, y, max_radius=radius, color=color))
        self.add_shake(3.5)

    def update(self):
        # Демпфирование тряски
        if self.shake_amount > 0:
            self.shake_amount = max(0.0, self.shake_amount - 0.7)

        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

        for s in self.shockwaves:
            s.update()
        self.shockwaves = [s for s in self.shockwaves if s.alive]

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
        for s in self.shockwaves:
            s.draw(surface)
        for b in self.beams:
            b.draw(surface)
        for l in self.lightnings:
            l.draw(surface)
        for p in self.particles:
            p.draw(surface)
        for t in self.floating_texts:
            t.draw(surface)