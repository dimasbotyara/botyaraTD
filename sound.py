# sound.py — Звуковой менеджер с поддержкой пользовательских внешних аудиофайлов

import pygame
import math
import os
import array

SOUNDS_DIR = "sounds"

class SoundManager:
    """Менеджер звуковых эффектов: гибридный синтезатор + загрузка внешних wav/mp3/ogg"""

    def __init__(self):
        self.enabled = True
        self.volume = 0.5
        self.sounds = {}

        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self._load_all_sounds()
        except Exception as e:
            print(f"Предупреждение: Не удалось инициализировать аудио: {e}")
            self.enabled = False

    def _make_sound(self, duration, waveform_fn):
        """Генерация синтезированного звука"""
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        buf = array.array('h')

        for i in range(n_samples):
            t = i / sample_rate
            val = waveform_fn(t, duration)
            val_int = int(max(-32768, min(32767, val * 32767 * self.volume)))
            buf.append(val_int)

        return pygame.mixer.Sound(buffer=buf)

    def _load_all_sounds(self):
        """Инициализация процедурных звуков (пулемет, золото, авиаудар) и внешних файлов"""

        # 1. Синтез пулемета
        def synth_mg(t, d):
            freq = 600 - t * 3000
            env = (1 - t/d)
            noise = (math.sin(t * 12345.678) * 0.4)
            return (math.sin(2 * math.pi * freq * t) * 0.6 + noise) * env

        # 2. Синтез золота
        def synth_gold(t, d):
            freq = 800 if t < d*0.5 else 1200
            env = math.exp(-(t % (d*0.5)) * 25)
            return math.sin(2 * math.pi * freq * t) * env

        # 3. Синтез авиаудара
        def synth_airstrike(t, d):
            freq = 100 + math.sin(t * 40) * 80
            env = math.exp(-t * 4)
            noise = math.sin(t * 33333.3) * 0.6
            return (math.sin(2 * math.pi * freq * t) * 0.4 + noise) * env

        # Процедурные звуки (оставляем)
        try:
            self.sounds["machinegun"] = self._make_sound(0.06, synth_mg)
            self.sounds["gold"] = self._make_sound(0.15, synth_gold)
            self.sounds["airstrike"] = self._make_sound(0.60, synth_airstrike)
        except Exception as e:
            print(f"Ошибка при синтезе базовых звуков: {e}")

        # Список звуков, которые пользователь может добавить в папку sounds/
        external_keys = [
            "sniper", "freeze", "cannon", "laser", "poison",
            "tesla", "missile", "explosion", "hit", "hurt",
            "click", "victory"
        ]

        # Автоматическая загрузка из папки sounds/ (если файлы существуют)
        for key in external_keys:
            loaded = False
            for ext in [".wav", ".mp3", ".ogg"]:
                file_path = os.path.join(SOUNDS_DIR, f"{key}{ext}")
                if os.path.exists(file_path):
                    try:
                        self.sounds[key] = pygame.mixer.Sound(file_path)
                        loaded = True
                        break
                    except Exception as e:
                        print(f"Не удалось загрузить {file_path}: {e}")
            if not loaded:
                self.sounds[key] = None  # Заглушка, если файла пока нет

    def play(self, sound_name):
        """Воспроизвести звук по названию"""
        if not self.enabled or sound_name not in self.sounds:
            return
        snd = self.sounds.get(sound_name)
        if snd is not None:
            try:
                snd.play()
            except Exception:
                pass

    def set_volume(self, volume):
        """Установить громкость 0.0 .. 1.0"""
        self.volume = max(0.0, min(1.0, volume))
        if self.volume == 0:
            self.enabled = False
        else:
            self.enabled = True
            for sound in self.sounds.values():
                if sound is not None:
                    try:
                        sound.set_volume(self.volume)
                    except Exception:
                        pass

# Глобальный экземпляр
sound_manager = SoundManager()
