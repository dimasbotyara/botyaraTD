# sound.py — Процедурный звуковой синтезатор на pygame.mixer
import pygame
import math
import array

class SoundManager:
    """Менеджер звуковых эффектов без сторонних аудиофайлов"""
    
    def __init__(self):
        self.enabled = True
        self.volume = 0.5
        self.sounds = {}
        
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self._generate_sounds()
        except Exception as e:
            print(f"Предупреждение: Не удалось инициализировать аудио: {e}")
            self.enabled = False

    def _make_sound(self, duration, waveform_fn):
        """Вспомогательный метод для генерации Pygame Sound из математической функции"""
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        buf = array.array('h')
        
        for i in range(n_samples):
            t = i / sample_rate
            val = waveform_fn(t, duration)
            # Ограничение 16-бит signed integer
            val_int = int(max(-32768, min(32767, val * 32767 * self.volume)))
            buf.append(val_int)
            
        return pygame.mixer.Sound(buffer=buf)

    def _generate_sounds(self):
        """Создать всю палитру звуковых эффектов"""
        
        # 1. Пулемёт (короткий щелчок/выстрел)
        def synth_mg(t, d):
            freq = 600 - t * 3000
            env = (1 - t/d)
            noise = (math.sin(t * 12345.678) * 0.4)
            return (math.sin(2 * math.pi * freq * t) * 0.6 + noise) * env

        # 2. Снайпер (громкий банг)
        def synth_sniper(t, d):
            freq = 900 - t * 4000
            env = math.exp(-t * 25)
            noise = (math.sin(t * 98765.43) * 0.6)
            return (math.sin(2 * math.pi * max(50, freq) * t) * 0.5 + noise) * env

        # 3. Заморозка (колокольчик/хруст)
        def synth_freeze(t, d):
            freq = 1200 + math.sin(t * 80) * 400
            env = math.exp(-t * 10)
            return math.sin(2 * math.pi * freq * t) * env

        # 4. Пушка (низкий бум)
        def synth_cannon(t, d):
            freq = max(40, 200 - t * 800)
            env = math.exp(-t * 12)
            noise = (math.sin(t * 54321.12) * 0.5)
            return (math.sin(2 * math.pi * freq * t) * 0.6 + noise) * env

        # 5. Лазер (пила / бластер)
        def synth_laser(t, d):
            freq = 1400 - t * 5000
            env = 1 - t/d
            return math.sin(2 * math.pi * freq * t) * env

        # 6. Яд (пузырение)
        def synth_poison(t, d):
            freq = 300 + math.sin(t * 120) * 150
            env = 1 - t/d
            return math.sin(2 * math.pi * freq * t) * env

        # 7. Тесла (электрический треск)
        def synth_tesla(t, d):
            env = math.exp(-t * 20)
            noise = (math.sin(t * 88888.88) * 0.8)
            freq = 800 + math.sin(t * 300) * 400
            return (math.sin(2 * math.pi * freq * t) * 0.3 + noise) * env

        # 8. Ракета (свист + взрыв)
        def synth_missile(t, d):
            freq = 400 + t * 600
            env = math.exp(-t * 8)
            return math.sin(2 * math.pi * freq * t) * env

        # 9. Взрыв
        def synth_explosion(t, d):
            env = math.exp(-t * 8)
            noise = math.sin(t * 77777.7)
            sub = math.sin(2 * math.pi * max(30, 120 - t * 300) * t)
            return (noise * 0.7 + sub * 0.5) * env

        # 10. Удар по врагу
        def synth_hit(t, d):
            freq = 150 - t * 500
            env = math.exp(-t * 40)
            return math.sin(2 * math.pi * max(30, freq) * t) * env

        # 11. Смерть врага / Золото (двойной динг)
        def synth_gold(t, d):
            freq = 800 if t < d*0.5 else 1200
            env = math.exp(-(t % (d*0.5)) * 25)
            return math.sin(2 * math.pi * freq * t) * env

        # 12. Потеря жизни
        def synth_hurt(t, d):
            freq = 180 - t * 200
            env = math.exp(-t * 10)
            return (math.sin(2 * math.pi * max(40, freq) * t) * 0.5 + math.sin(t * 1234.5) * 0.5) * env

        # 13. Авиаудар
        def synth_airstrike(t, d):
            freq = 100 + math.sin(t * 40) * 80
            env = math.exp(-t * 4)
            noise = math.sin(t * 33333.3) * 0.6
            return (math.sin(2 * math.pi * freq * t) * 0.4 + noise) * env

        # 14. Кнопка UI
        def synth_click(t, d):
            freq = 800 - t * 2000
            env = math.exp(-t * 50)
            return math.sin(2 * math.pi * max(100, freq) * t) * env

        # 15. Победа (фанфара arpeggio)
        def synth_victory(t, d):
            notes = [523.25, 659.25, 783.99, 1046.50]  # C, E, G, C
            idx = min(3, int(t / (d / 4)))
            freq = notes[idx]
            env = math.exp(-(t % (d / 4)) * 12)
            return math.sin(2 * math.pi * freq * t) * env

        # Создаём экземпляры звуков
        try:
            self.sounds = {
                "machinegun": self._make_sound(0.06, synth_mg),
                "sniper": self._make_sound(0.18, synth_sniper),
                "freeze": self._make_sound(0.15, synth_freeze),
                "cannon": self._make_sound(0.22, synth_cannon),
                "laser": self._make_sound(0.08, synth_laser),
                "poison": self._make_sound(0.12, synth_poison),
                "tesla": self._make_sound(0.12, synth_tesla),
                "missile": self._make_sound(0.20, synth_missile),
                "explosion": self._make_sound(0.35, synth_explosion),
                "hit": self._make_sound(0.05, synth_hit),
                "gold": self._make_sound(0.15, synth_gold),
                "hurt": self._make_sound(0.25, synth_hurt),
                "airstrike": self._make_sound(0.60, synth_airstrike),
                "click": self._make_sound(0.04, synth_click),
                "victory": self._make_sound(0.50, synth_victory),
            }
        except Exception as e:
            print(f"Ошибка при генерации звуков: {e}")

    def play(self, sound_name):
        """Воспроизвести звук по названию"""
        if not self.enabled or sound_name not in self.sounds:
            return
        try:
            self.sounds[sound_name].play()
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
                sound.set_volume(self.volume)

# Глобальный синглтон звуков
sound_manager = SoundManager()
