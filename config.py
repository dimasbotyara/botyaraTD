# config.py — Настройки и локализация (RU / EN)

import json
import os

CONFIG_FILE = "config.json"

# Словари перевода (RU / EN)
TRANSLATIONS = {
    "ru": {
        "title": "botyaraTD",
        "subtitle": "Deluxe Edition & 5 Уровней",
        "play": "ВЫБОР УРОВНЯ",
        "settings": "НАСТРОЙКИ",
        "quit": "ВЫХОД",
        "level_select": "ВЫБОР УРОВНЯ",
        "play_level": "ИГРАТЬ УРОВЕНЬ",
        "back": "НАЗАД",
        "back_to_menu": "НАЗАД В МЕНЮ",
        "difficulty": "Сложность",
        "diff_0": "Легко",
        "diff_1": "Нормально",
        "diff_2": "Сложно",
        "diff_3": "Эксперт",
        "diff_4": "Апокалипсис",
        "diff_desc_0": "Больше золота, меньше врагов",
        "diff_desc_1": "Стандартный баланс",
        "diff_desc_2": "Меньше золота, враги сильнее",
        "volume": "Громкость",
        "language": "Язык / Language",
        "wave": "Волна",
        "lives": "Жизни",
        "gold": "Золото",
        "towers": "БАШНИ",
        "abilities": "СПОСОБНОСТИ",
        "start_wave": "НАЧАТЬ ВОЛНУ",
        "wave_in_progress": "ВОЛНА ИДЁТ...",
        "speed": "Скорость",
        "sell": "Продать",
        "upgrade": "Улучшить",
        "max": "МАКС",
        "damage": "Урон",
        "range": "Радиус",
        "rate": "Скор.",
        "record": "🏆 Рекорд",
        "kills": "Убито",
        "locked": "🔒 ЗАБЛОКИРОВАНО",
        "pass_prev": "Пройдите предыдущий уровень!",
        "pause": "ПАУЗА",
        "resume": "ПРОДОЛЖИТЬ",
        "menu": "В МЕНЮ",
        "victory": "ПОБЕДА!",
        "defeat": "ПОРАЖЕНИЕ",
        "you_defended": "Ты защитил базу!",
        "try_again": "Попробуй другую стратегию!",
        "ability_airstrike": "[BOMB] Авиаудар",
        "ability_freeze": "[ICE] Заморозка",
        "ability_gold": "[GOLD] Лихорадка",
        "hint_upgrade": "💡 Кликни по башне на карте для меню прокачки",
        "controls": "Управление:",
        "controls_1": "1-8 — Выбор башни  |  Q, W, E — Способности",
        "controls_2": "Стрелки ЛЕВО / ПРАВО — Выбор уровня",
        "controls_3": "ESC — Пауза / Назад  |  F9 — Скрыть окно",
    },
    "en": {
        "title": "botyaraTD",
        "subtitle": "Deluxe Edition & 5 Levels",
        "play": "SELECT LEVEL",
        "settings": "SETTINGS",
        "quit": "QUIT",
        "level_select": "SELECT LEVEL",
        "play_level": "PLAY LEVEL",
        "back": "BACK",
        "back_to_menu": "MAIN MENU",
        "difficulty": "Difficulty",
        "diff_0": "Easy",
        "diff_1": "Normal",
        "diff_2": "Hard",
        "diff_3": "Expert",
        "diff_4": "Apocalypse",
        "diff_desc_0": "More gold, fewer enemies",
        "diff_desc_1": "Balanced difficulty",
        "diff_desc_2": "Less gold, stronger enemies",
        "volume": "Volume",
        "language": "Language / Язык",
        "wave": "Wave",
        "lives": "Lives",
        "gold": "Gold",
        "towers": "TOWERS",
        "abilities": "ABILITIES",
        "start_wave": "START WAVE",
        "wave_in_progress": "WAVE IN PROGRESS...",
        "speed": "Speed",
        "sell": "Sell",
        "upgrade": "Upgrade",
        "max": "MAX",
        "damage": "Damage",
        "range": "Range",
        "rate": "Rate",
        "record": "🏆 Best",
        "kills": "Kills",
        "locked": "🔒 LOCKED",
        "pass_prev": "Complete previous level first!",
        "pause": "PAUSED",
        "resume": "RESUME",
        "menu": "MAIN MENU",
        "victory": "VICTORY!",
        "defeat": "DEFEAT",
        "you_defended": "Base defended successfully!",
        "try_again": "Try another strategy!",
        "ability_airstrike": "[BOMB] Airstrike",
        "ability_freeze": "[ICE] Cryo Freeze",
        "ability_gold": "[GOLD] Gold Rush",
        "hint_upgrade": "💡 Click tower on map to upgrade or sell",
        "controls": "Controls:",
        "controls_1": "1-8 — Select tower  |  Q, W, E — Abilities",
        "controls_2": "LEFT / RIGHT arrows — Level navigation",
        "controls_3": "ESC — Pause / Back  |  F9 — Hide window",
    }
}


class ConfigManager:
    """Управление настройками и языком"""

    def __init__(self):
        self.language = "ru"  # "ru" или "en"
        self.volume = 0.5
        self.difficulty = 1
        self.load_config()

    def load_config(self):
        """Загрузка конфигурации из файла config.json в папке скрипта"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.language = data.get("language", "ru")
                    self.volume = float(data.get("volume", 0.5))
                    self.difficulty = int(data.get("difficulty", 1))
            except Exception as e:
                print(f"Ошибка загрузки config.json: {e}")

    def save_config(self):
        """Сохранение конфигурации в файл config.json"""
        try:
            data = {
                "language": self.language,
                "volume": self.volume,
                "difficulty": self.difficulty,
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения config.json: {e}")

    def toggle_language(self):
        """Переключение языка RU <-> EN"""
        self.language = "en" if self.language == "ru" else "ru"
        self.save_config()

    def t(self, key):
        """Получить переведенную строку по ключу"""
        lang_dict = TRANSLATIONS.get(self.language, TRANSLATIONS["ru"])
        return lang_dict.get(key, key)


config_manager = ConfigManager()


def t(key):
    """Быстрый хелпер вызова перевода"""
    return config_manager.t(key)
