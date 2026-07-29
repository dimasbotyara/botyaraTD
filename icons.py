# icons.py — Векторная отрисовка ярких иконок (Бомба, Лёд, Золото, Кубок, Замок, Звезда)

import pygame
import math

def draw_bomb_icon(surface, x, y, size=18):
    """Отрисовка иконки бомбы 💣"""
    r = size // 2 - 2
    cx, cy = x + size // 2, y + size // 2 + 1
    # Тело бомбы
    pygame.draw.circle(surface, (30, 30, 40), (cx, cy), r)
    pygame.draw.circle(surface, (80, 80, 100), (cx - r//3, cy - r//3), r//3)
    # Фитиль
    pygame.draw.arc(surface, (200, 150, 80), (cx - 2, cy - r - 6, 8, 8), 0, 3.14, 2)
    # Искра
    pygame.draw.circle(surface, (255, 200, 50), (cx + 4, cy - r - 4), 2)
    pygame.draw.circle(surface, (255, 80, 30), (cx + 4, cy - r - 4), 1)

def draw_ice_icon(surface, x, y, size=18):
    """Отрисовка иконки льда/снежинки ❄️"""
    cx, cy = x + size // 2, y + size // 2
    r = size // 2 - 2
    for angle_deg in range(0, 360, 60):
        rad = math.radians(angle_deg)
        ex = cx + math.cos(rad) * r
        ey = cy + math.sin(rad) * r
        pygame.draw.line(surface, (150, 220, 255), (cx, cy), (int(ex), int(ey)), 2)
        # Ответвления снежинки
        hx = cx + math.cos(rad) * (r * 0.6)
        hy = cy + math.sin(rad) * (r * 0.6)
        p_rad1 = math.radians(angle_deg + 45)
        p_rad2 = math.radians(angle_deg - 45)
        pygame.draw.line(surface, (200, 240, 255), (int(hx), int(hy)),
                         (int(hx + math.cos(p_rad1)*3), int(hy + math.sin(p_rad1)*3)), 1)
        pygame.draw.line(surface, (200, 240, 255), (int(hx), int(hy)),
                         (int(hx + math.cos(p_rad2)*3), int(hy + math.sin(p_rad2)*3)), 1)

def draw_gold_icon(surface, x, y, size=18):
    """Отрисовка иконки монетки 💰"""
    cx, cy = x + size // 2, y + size // 2
    r = size // 2 - 1
    pygame.draw.circle(surface, (255, 215, 0), (cx, cy), r)
    pygame.draw.circle(surface, (200, 150, 0), (cx, cy), r, 1)
    # Знак $
    font = pygame.font.Font(None, int(size * 0.85))
    txt = font.render("$", True, (120, 80, 0))
    surface.blit(txt, txt.get_rect(center=(cx, cy)))

def draw_trophy_icon(surface, x, y, size=18):
    """Отрисовка иконки кубка 🏆"""
    cx, cy = x + size // 2, y + size // 2
    # Кубок
    cup_rect = pygame.Rect(cx - 6, cy - 7, 12, 8)
    pygame.draw.rect(surface, (255, 215, 0), cup_rect, border_bottom_left_radius=4, border_bottom_right_radius=4)
    # Ножка
    pygame.draw.line(surface, (200, 160, 0), (cx, cy + 1), (cx, cy + 5), 2)
    pygame.draw.line(surface, (200, 160, 0), (cx - 4, cy + 5), (cx + 4, cy + 5), 2)
    # Ручки
    pygame.draw.arc(surface, (255, 215, 0), (cx - 9, cy - 6, 6, 6), 1.5, 4.7, 1)
    pygame.draw.arc(surface, (255, 215, 0), (cx + 3, cy - 6, 6, 6), 4.7, 1.5, 1)

def draw_lock_icon(surface, x, y, size=18):
    """Отрисовка иконки замка 🔒"""
    cx, cy = x + size // 2, y + size // 2
    # Дужка
    pygame.draw.arc(surface, (200, 200, 210), (cx - 5, cy - 8, 10, 10), 0, 3.14, 2)
    # Корпус
    body = pygame.Rect(cx - 6, cy - 2, 12, 9)
    pygame.draw.rect(surface, (220, 160, 40), body, border_radius=2)
    # Замочная скважина
    pygame.draw.circle(surface, (50, 40, 10), (cx, cy + 2), 2)

def draw_star_icon(surface, x, y, size=18, filled=True):
    """Отрисовка иконки звезды ⭐"""
    cx, cy = x + size // 2, y + size // 2
    r_outer = size // 2 - 1
    r_inner = r_outer * 0.4
    points = []
    for i in range(10):
        r = r_outer if i % 2 == 0 else r_inner
        angle = i * (math.pi / 5) - math.pi / 2
        px = cx + math.cos(angle) * r
        py = cy + math.sin(angle) * r
        points.append((px, py))
    
    color = (255, 215, 0) if filled else (100, 100, 110)
    pygame.draw.polygon(surface, color, points)
    border_col = (180, 130, 0) if filled else (60, 60, 70)
    pygame.draw.polygon(surface, border_col, points, 1)
