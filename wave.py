# wave.py — Система волн врагов

from settings import MAX_WAVES


def get_wave(wave_num):
    """
    Возвращает список врагов для волны.
    Каждый элемент: (тип_врага, задержка_перед_спавном_в_кадрах)
    """
    enemies = []

    if wave_num == 1:
        # Простое начало
        for i in range(8):
            enemies.append(("basic", 30))

    elif wave_num == 2:
        for i in range(10):
            enemies.append(("basic", 25))

    elif wave_num == 3:
        for i in range(6):
            enemies.append(("basic", 25))
        for i in range(4):
            enemies.append(("fast", 20))

    elif wave_num == 4:
        for i in range(12):
            enemies.append(("basic", 22))
        enemies.append(("tank", 40))

    elif wave_num == 5:
        # Первый босс!
        for i in range(8):
            enemies.append(("basic", 20))
        for i in range(5):
            enemies.append(("fast", 15))
        enemies.append(("boss", 60))

    elif wave_num == 6:
        for i in range(15):
            enemies.append(("swarm", 10))
        for i in range(3):
            enemies.append(("tank", 35))

    elif wave_num == 7:
        for i in range(8):
            enemies.append(("basic", 20))
        for i in range(4):
            enemies.append(("shield", 30))

    elif wave_num == 8:
        for i in range(6):
            enemies.append(("fast", 15))
        for i in range(3):
            enemies.append(("healer", 40))
        for i in range(6):
            enemies.append(("basic", 20))

    elif wave_num == 9:
        for i in range(5):
            enemies.append(("split", 35))
        for i in range(8):
            enemies.append(("fast", 15))

    elif wave_num == 10:
        # Второй босс!
        for i in range(10):
            enemies.append(("basic", 18))
        for i in range(5):
            enemies.append(("tank", 30))
        for i in range(2):
            enemies.append(("healer", 40))
        enemies.append(("boss", 60))

    elif wave_num == 11:
        for i in range(20):
            enemies.append(("swarm", 8))
        for i in range(4):
            enemies.append(("shield", 25))

    elif wave_num == 12:
        for i in range(6):
            enemies.append(("ghost", 25))
        for i in range(8):
            enemies.append(("basic", 18))
        for i in range(3):
            enemies.append(("tank", 30))

    elif wave_num == 13:
        for i in range(8):
            enemies.append(("split", 25))
        for i in range(6):
            enemies.append(("fast", 12))
        for i in range(2):
            enemies.append(("healer", 35))

    elif wave_num == 14:
        for i in range(10):
            enemies.append(("shield", 20))
        for i in range(10):
            enemies.append(("ghost", 18))

    elif wave_num == 15:
        # Третий босс!
        for i in range(25):
            enemies.append(("swarm", 6))
        for i in range(5):
            enemies.append(("tank", 25))
        for i in range(3):
            enemies.append(("healer", 30))
        enemies.append(("boss", 50))
        enemies.append(("boss", 80))

    elif wave_num == 16:
        for i in range(12):
            enemies.append(("fast", 10))
        for i in range(6):
            enemies.append(("ghost", 20))
        for i in range(4):
            enemies.append(("split", 25))

    elif wave_num == 17:
        for i in range(8):
            enemies.append(("tank", 20))
        for i in range(4):
            enemies.append(("healer", 25))
        for i in range(6):
            enemies.append(("shield", 20))

    elif wave_num == 18:
        for i in range(30):
            enemies.append(("swarm", 5))
        for i in range(8):
            enemies.append(("split", 18))

    elif wave_num == 19:
        for i in range(10):
            enemies.append(("ghost", 15))
        for i in range(10):
            enemies.append(("shield", 15))
        for i in range(5):
            enemies.append(("tank", 20))

    elif wave_num == 20:
        # Мега-босс!
        for i in range(15):
            enemies.append(("basic", 12))
        for i in range(10):
            enemies.append(("fast", 10))
        for i in range(5):
            enemies.append(("tank", 20))
        for i in range(3):
            enemies.append(("healer", 25))
        enemies.append(("mega_boss", 80))

    elif wave_num == 21:
        for i in range(12):
            enemies.append(("ghost", 12))
        for i in range(12):
            enemies.append(("split", 15))
        for i in range(6):
            enemies.append(("shield", 18))

    elif wave_num == 22:
        for i in range(8):
            enemies.append(("tank", 15))
        for i in range(5):
            enemies.append(("healer", 20))
        for i in range(35):
            enemies.append(("swarm", 4))

    elif wave_num == 23:
        for i in range(15):
            enemies.append(("shield", 12))
        for i in range(15):
            enemies.append(("ghost", 10))
        for i in range(5):
            enemies.append(("split", 15))
        enemies.append(("boss", 40))

    elif wave_num == 24:
        for i in range(10):
            enemies.append(("tank", 12))
        for i in range(8):
            enemies.append(("healer", 15))
        for i in range(20):
            enemies.append(("fast", 6))
        for i in range(10):
            enemies.append(("split", 10))
        enemies.append(("boss", 40))
        enemies.append(("boss", 50))

    elif wave_num == 25:
        # ФИНАЛЬНАЯ ВОЛНА!
        for i in range(40):
            enemies.append(("swarm", 4))
        for i in range(15):
            enemies.append(("tank", 10))
        for i in range(10):
            enemies.append(("healer", 12))
        for i in range(10):
            enemies.append(("shield", 10))
        for i in range(10):
            enemies.append(("ghost", 10))
        for i in range(8):
            enemies.append(("split", 12))
        enemies.append(("boss", 40))
        enemies.append(("boss", 50))
        enemies.append(("mega_boss", 80))
        enemies.append(("mega_boss", 100))

    else:
        # На всякий случай — бесконечный режим
        count = 10 + wave_num * 2
        for i in range(count):
            enemies.append(("basic", max(5, 20 - wave_num)))

    return enemies