# settings.py — Все константы и настройки игры

import pygame

# === ОКНО ===
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
SIDEBAR_WIDTH = 250
GAME_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH
GAME_HEIGHT = WINDOW_HEIGHT
FPS = 60
TITLE = "botyaraTD"

# === СЕТКА ===
CELL_SIZE = 40
GRID_COLS = GAME_WIDTH // CELL_SIZE
GRID_ROWS = GAME_HEIGHT // CELL_SIZE

# === ЦВЕТА ===
# Основные
BLACK = (10, 10, 15)
WHITE = (255, 255, 255)
GRAY = (130, 130, 130)
DARK_GRAY = (50, 50, 60)
LIGHT_GRAY = (200, 200, 210)

# Природа
GRASS_1 = (34, 120, 50)
GRASS_2 = (40, 135, 55)
PATH_COLOR = (140, 110, 70)
PATH_BORDER = (110, 85, 50)

# UI
UI_BG = (25, 25, 40)
UI_PANEL = (35, 35, 55)
UI_BORDER = (60, 60, 90)
UI_HOVER = (50, 50, 75)
UI_SELECTED = (70, 70, 120)

# Кнопки
BTN_GREEN = (40, 180, 70)
BTN_GREEN_HOVER = (50, 210, 85)
BTN_RED = (200, 50, 50)
BTN_RED_HOVER = (230, 70, 70)
BTN_BLUE = (40, 100, 200)
BTN_BLUE_HOVER = (55, 125, 230)
BTN_YELLOW = (200, 180, 30)
BTN_YELLOW_HOVER = (230, 210, 50)

# Золото
GOLD_COLOR = (255, 215, 0)

# HP бар
HP_GREEN = (50, 220, 70)
HP_YELLOW = (230, 200, 30)
HP_RED = (220, 50, 40)
HP_BG = (40, 40, 40)

# Башни
TOWER_COLORS = {
    "machinegun": (100, 100, 110),
    "sniper": (60, 60, 150),
    "freeze": (100, 200, 255),
    "cannon": (180, 80, 30),
    "laser": (255, 50, 50),
    "poison": (80, 200, 80),
    "tesla": (180, 130, 255),
    "missile": (200, 200, 60),
}

TOWER_COLORS_DARK = {
    "machinegun": (70, 70, 80),
    "sniper": (40, 40, 110),
    "freeze": (60, 140, 200),
    "cannon": (130, 55, 20),
    "laser": (180, 30, 30),
    "poison": (50, 140, 50),
    "tesla": (120, 80, 200),
    "missile": (150, 150, 40),
}

# Враги
ENEMY_COLORS = {
    "basic": (60, 200, 80),
    "fast": (255, 220, 50),
    "tank": (200, 60, 60),
    "healer": (255, 150, 200),
    "shield": (100, 150, 255),
    "swarm": (200, 150, 50),
    "ghost": (180, 180, 220),
    "boss": (180, 40, 220),
    "mega_boss": (255, 50, 50),
    "split": (255, 140, 50),
}

# === БАШНИ (статы) ===
# damage, fire_rate (кадры между выстрелами), range (пиксели), cost
TOWER_STATS = {
    "machinegun": {
        "name": "Пулемёт",
        "desc": "Быстрая стрельба",
        "levels": [
            {"damage": 8, "fire_rate": 12, "range": 120, "cost": 50},
            {"damage": 14, "fire_rate": 10, "range": 135, "cost": 40},
            {"damage": 22, "fire_rate": 8, "range": 150, "cost": 60},
        ]
    },
    "sniper": {
        "name": "Снайпер",
        "desc": "Дальний урон",
        "levels": [
            {"damage": 40, "fire_rate": 50, "range": 250, "cost": 100},
            {"damage": 70, "fire_rate": 45, "range": 280, "cost": 70},
            {"damage": 110, "fire_rate": 40, "range": 320, "cost": 100},
        ]
    },
    "freeze": {
        "name": "Заморозка",
        "desc": "Замедляет врагов",
        "levels": [
            {"damage": 3, "fire_rate": 25, "range": 110, "cost": 75, "slow": 0.4, "slow_duration": 90},
            {"damage": 5, "fire_rate": 22, "range": 125, "cost": 55, "slow": 0.5, "slow_duration": 110},
            {"damage": 8, "fire_rate": 18, "range": 145, "cost": 80, "slow": 0.6, "slow_duration": 130},
        ]
    },
    "cannon": {
        "name": "Пушка",
        "desc": "Урон по площади",
        "levels": [
            {"damage": 25, "fire_rate": 55, "range": 130, "cost": 125, "splash": 50},
            {"damage": 45, "fire_rate": 50, "range": 145, "cost": 80, "splash": 60},
            {"damage": 70, "fire_rate": 45, "range": 160, "cost": 110, "splash": 75},
        ]
    },
    "laser": {
        "name": "Лазер",
        "desc": "Луч прожигает",
        "levels": [
            {"damage": 1.5, "fire_rate": 1, "range": 140, "cost": 150},
            {"damage": 2.5, "fire_rate": 1, "range": 160, "cost": 100},
            {"damage": 4.0, "fire_rate": 1, "range": 180, "cost": 130},
        ]
    },
    "poison": {
        "name": "Яд",
        "desc": "Урон со временем",
        "levels": [
            {"damage": 5, "fire_rate": 40, "range": 120, "cost": 80, "dot": 2, "dot_duration": 120},
            {"damage": 8, "fire_rate": 35, "range": 135, "cost": 60, "dot": 3, "dot_duration": 150},
            {"damage": 12, "fire_rate": 30, "range": 150, "cost": 90, "dot": 5, "dot_duration": 180},
        ]
    },
    "tesla": {
        "name": "Тесла",
        "desc": "Молния по цепи",
        "levels": [
            {"damage": 15, "fire_rate": 35, "range": 130, "cost": 175, "chain": 3},
            {"damage": 25, "fire_rate": 30, "range": 145, "cost": 120, "chain": 4},
            {"damage": 40, "fire_rate": 25, "range": 160, "cost": 150, "chain": 5},
        ]
    },
    "missile": {
        "name": "Ракетница",
        "desc": "Самонаводящиеся",
        "levels": [
            {"damage": 35, "fire_rate": 60, "range": 180, "cost": 200, "splash": 40},
            {"damage": 55, "fire_rate": 55, "range": 200, "cost": 130, "splash": 50},
            {"damage": 80, "fire_rate": 50, "range": 220, "cost": 160, "splash": 65},
        ]
    },
}

# === ВРАГИ (статы) ===
# hp, speed (пикселей/кадр), reward
ENEMY_STATS = {
    "basic": {"name": "Солдат", "hp": 60, "speed": 1.2, "reward": 10},
    "fast": {"name": "Бегун", "hp": 35, "speed": 2.5, "reward": 15},
    "tank": {"name": "Танк", "hp": 250, "speed": 0.7, "reward": 30},
    "healer": {"name": "Медик", "hp": 80, "speed": 1.0, "reward": 25, "heal_range": 80, "heal_amount": 0.3},
    "shield": {"name": "Щитоносец", "hp": 150, "speed": 1.0, "reward": 20, "shield_hp": 80},
    "swarm": {"name": "Рой", "hp": 20, "speed": 1.8, "reward": 5},
    "ghost": {"name": "Призрак", "hp": 70, "speed": 1.5, "reward": 20, "stealth_chance": 0.3},
    "split": {"name": "Делитель", "hp": 100, "speed": 1.0, "reward": 20, "split_into": 2},
    "boss": {"name": "Босс", "hp": 800, "speed": 0.5, "reward": 100},
    "mega_boss": {"name": "Мега-Босс", "hp": 2000, "speed": 0.4, "reward": 250},
}

# === ВОЛНЫ ===
MAX_WAVES = 25

# === ИГРОК ===
START_GOLD = 250
START_LIVES = 25
SELL_RATIO = 0.6  # Возврат 60% при продаже

# === СКОРОСТЬ ИГРЫ ===
SPEED_NORMAL = 1
SPEED_FAST = 3

# === СЕКРЕТНАЯ КНОПКА ===
HIDE_KEY = pygame.K_F9
PAUSE_KEY = pygame.K_ESCAPE