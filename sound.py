# sound.py — Звуковой менеджер с поддержкой пользовательских внешних аудиофайлов

import pygame
import math
import os
import array
import logging
from pathlib import Path

from config import config_manager

SOUNDS_DIR = Path(__file__).resolve().parent / "sounds"
logger = logging.getLogger(__name__)

class SoundManager:
    """Менеджер звуковых эффектов: гибридный синтезатор + загрузка внешних wav/mp3/ogg"""

    MAX_CHANNELS = 8
    # Интервалы в реальных мс: скорость симуляции не увеличивает частоту звука.
    REPEAT_INTERVAL_MS = {"machinegun": 60, "gold": 100, "laser": 100,
                          "hit": 60, "explosion": 100, "airstrike": 250}

    def __init__(self):
        self.enabled = False
        self.volume = max(0.0, min(1.0, config_manager.volume))
        self.sounds = {}
        self.channels = []
        self._last_played = {}
        self._audio_ready = False

        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            pygame.mixer.set_num_channels(self.MAX_CHANNELS)
            self.channels = [pygame.mixer.Channel(i) for i in range(self.MAX_CHANNELS)]
            self._load_all_sounds()
            self._audio_ready = True
            self.enabled = self.volume > 0
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
            val_int = int(max(-32768, min(32767, val * 32767)))
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
        missing = []
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
                self.sounds[key] = None
                missing.append(key)

        if missing:
            logger.warning("Отсутствуют или не загрузились звуки в %s: %s",
                           SOUNDS_DIR, ", ".join(missing))

    def _set_channel_gains(self, active):
        # Суммарный gain не превышает master volume даже при совпадении пиков.
        gain = self.volume / max(1, len(active))
        for channel in active:
            channel.set_volume(gain)

    def update(self):
        """Пересчитать уровень после завершения коротких эффектов (раз в кадр)."""
        if not self._audio_ready:
            return
        self._set_channel_gains([channel for channel in self.channels if channel.get_busy()])

    def play(self, sound_name):
        """Ограничить повторы и тихо смешать одновременно звучащие эффекты."""
        snd = self.sounds.get(sound_name)
        if not self.enabled or snd is None:
            return
        now = pygame.time.get_ticks()
        interval = self.REPEAT_INTERVAL_MS.get(sound_name, 40)
        last = self._last_played.get(sound_name)
        if last is not None and now - last < interval:
            return
        active = [channel for channel in self.channels if channel.get_busy()]
        free = next((channel for channel in self.channels if channel not in active), None)
        if free is None:
            return  # Не обрываем существующие звуки и не создаём неограниченный хор.
        try:
            # Приглушаем все каналы ДО старта нового, чтобы не было громкого пика.
            self._set_channel_gains(active + [free])
            free.play(snd)
            self._last_played[sound_name] = now
        except pygame.error:
            self.update()

    def set_volume(self, volume):
        """Master volume применяется один раз, одинаково к синтезу и файлам."""
        self.volume = max(0.0, min(1.0, volume))
        self.enabled = self._audio_ready and self.volume > 0
        self.update()


# Глобальный экземпляр
sound_manager = SoundManager()
