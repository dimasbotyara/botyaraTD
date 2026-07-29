# highscores.py — Сохранение и загрузка рекордов игрока по уровням

import json
import os

HIGHSCORES_FILE = "highscores.json"

class HighscoreManager:
    """Управление рекордами для всех 5 уровней"""
    
    def __init__(self):
        self.scores = self.load_scores()

    def load_scores(self):
        """Загрузить рекорды из JSON файла"""
        if os.path.exists(HIGHSCORES_FILE):
            try:
                with open(HIGHSCORES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data
            except Exception as e:
                print(f"Ошибка загрузки рекордов: {e}")
        
        # Дефолтные рекорды
        return {
            str(i): {"best_wave": 0, "best_kills": 0, "completed": False}
            for i in range(5)
        }

    def save_scores(self):
        """Сохранить рекорды в JSON файл"""
        try:
            with open(HIGHSCORES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.scores, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения рекордов: {e}")

    def get_score(self, level_idx):
        """Получить рекорд для уровня (0..4)"""
        key = str(level_idx)
        return self.scores.get(key, {"best_wave": 0, "best_kills": 0, "completed": False})

    def is_level_unlocked(self, level_idx):
        """Открыт ли уровень для игры (уровень 0 открыт всегда, остальные открываются после прохождения предыдущего)"""
        if level_idx <= 0:
            return True
        prev = self.get_score(level_idx - 1)
        return prev.get("completed", False)

    def update_score(self, level_idx, wave_num, kills, won=False):
        """Обновить рекорд если результат лучше предыдущего"""
        key = str(level_idx)
        current = self.get_score(level_idx)
        
        updated = False
        if wave_num > current["best_wave"]:
            current["best_wave"] = wave_num
            updated = True
        if kills > current["best_kills"]:
            current["best_kills"] = kills
            updated = True
        if won and not current["completed"]:
            current["completed"] = True
            updated = True

        if updated:
            self.scores[key] = current
            self.save_scores()
        return updated

highscore_manager = HighscoreManager()
