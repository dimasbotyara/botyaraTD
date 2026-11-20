import json
from unittest.mock import Mock

import pygame
import pytest

import config
import highscores
import sound
from config import ConfigManager, config_manager, t
from effects import EffectsManager
from enemy import Enemy
from highscores import HighscoreManager
from map_data import LEVEL_DATA, get_level_info, get_map, get_path, is_buildable
from settings import CELL_SIZE, GRID_COLS, GRID_ROWS, GAME_WIDTH, GAME_HEIGHT
from ui import SettingsMenu


def test_shake_setting_roundtrip_and_legacy_default(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_FILE", str(path))
    path.write_text('{"volume": 0.25, "difficulty": 2}')
    settings = ConfigManager()
    assert settings.screen_shake is True
    settings.screen_shake = False
    settings.save_config()
    restored = ConfigManager()
    assert restored.screen_shake is False
    assert restored.volume == 0.25
    assert restored.difficulty == 2


def test_disabling_shake_clears_existing_and_prevents_new_shakes(monkeypatch):
    effects = EffectsManager()
    effects.add_shake(12)
    assert effects.shake_amount == 12
    monkeypatch.setattr(config_manager, "screen_shake", False)
    assert effects.get_shake_offset() == (0, 0)
    assert effects.shake_amount == 0
    effects.add_airstrike_explosion(100, 100)
    assert effects.shake_amount == 0
    assert effects.particles  # Explosions themselves remain visible.
    monkeypatch.setattr(config_manager, "screen_shake", True)
    assert effects.get_shake_offset() == (0, 0)
    effects.add_shake(4)
    assert effects.shake_amount == 4


@pytest.mark.parametrize("language", ["ru", "en"])
def test_shake_menu_button_toggles_and_localizes(monkeypatch, language):
    monkeypatch.setattr(config_manager, "language", language)
    save = Mock()
    monkeypatch.setattr(config_manager, "save_config", save)
    menu = SettingsMenu()
    menu.toggle_screen_shake()
    menu.update(menu.shake_btn.rect.center)
    assert config_manager.screen_shake is False
    assert menu.shake_btn.is_clicked(menu.shake_btn.rect.center, True)
    assert t("screen_shake") in menu.shake_btn.text
    assert t("off") in menu.shake_btn.text
    save.assert_called_once()
    assert menu.diff_btn.rect.bottom < menu.shake_btn.rect.top
    assert menu.shake_btn.rect.bottom < 420  # Controls start here.
    menu.draw(pygame.Surface((1200, 700)))


class FakeChannel:
    def __init__(self):
        self.busy = False
        self.volume = 1.0
        self.played = []

    def get_busy(self):
        return self.busy

    def set_volume(self, volume):
        self.volume = volume

    def play(self, effect):
        # Record volume at playback start, not just after normalization.
        self.played.append((effect, self.volume))
        self.busy = True


@pytest.fixture
def audio(monkeypatch):
    monkeypatch.setattr(sound.SoundManager, "_load_all_sounds", lambda self: None)
    monkeypatch.setattr(pygame.mixer, "Channel", lambda index: FakeChannel())
    manager = sound.SoundManager()
    manager.sounds = {name: object() for name in ("machinegun", "laser", "gold", "hit", "airstrike")}
    return manager


def test_overlap_volume_budget_and_recovery(audio):
    for name in ("machinegun", "gold", "airstrike"):
        audio.play(name)
    active = [channel for channel in audio.channels if channel.busy]
    assert len(active) == 3
    assert sum(channel.volume for channel in active) == pytest.approx(audio.volume)
    assert active[-1].played[0][1] == pytest.approx(audio.volume / 3)
    active[0].busy = active[1].busy = False
    audio.update()
    assert active[2].volume == pytest.approx(audio.volume)


def test_repeated_sounds_use_real_time_and_do_not_stack_at_x3(audio, monkeypatch):
    now = [1000]
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])
    for _ in range(3 * 60):
        audio.play("machinegun")
    assert sum(len(channel.played) for channel in audio.channels) == 1
    now[0] += 60
    audio.play("machinegun")
    assert sum(len(channel.played) for channel in audio.channels) == 2


def test_full_channel_pool_drops_excess_without_interrupting(audio, monkeypatch):
    now = [0]
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])
    for _ in range(30):
        now[0] += 100
        audio.play("gold")
    assert sum(len(channel.played) for channel in audio.channels) == audio.MAX_CHANNELS
    assert sum(channel.volume for channel in audio.channels) <= audio.volume + 1e-9


def test_mute_and_master_volume_apply_to_active_channels(audio):
    audio.play("airstrike")
    channel = audio.channels[0]
    audio.set_volume(0)
    assert channel.volume == 0
    assert not audio.enabled
    audio.play("gold")
    assert not audio.channels[1].played
    audio.set_volume(0.25)
    assert audio.enabled
    assert channel.volume == 0.25


def test_startup_uses_saved_volume(monkeypatch):
    monkeypatch.setattr(config_manager, "volume", 0)
    monkeypatch.setattr(sound.SoundManager, "_load_all_sounds", lambda self: None)
    manager = sound.SoundManager()
    assert manager.volume == 0
    assert not manager.enabled


def test_audio_failure_cannot_be_reenabled_by_volume(monkeypatch):
    def fail(**kwargs):
        raise pygame.error("no audio device")
    monkeypatch.setattr(pygame.mixer, "init", fail)
    manager = sound.SoundManager()
    manager.set_volume(1)
    assert not manager.enabled
    manager.play("gold")
    manager.update()


def test_synthesis_does_not_bake_in_master_volume(audio):
    audio.volume = 0.25
    quiet = audio._make_sound(0.01, lambda time, duration: 0.5).get_raw()
    audio.volume = 1
    loud = audio._make_sound(0.01, lambda time, duration: 0.5).get_raw()
    assert quiet == loud


@pytest.mark.parametrize("level", [5, 6, 7])
def test_new_maps_have_complete_unbranched_paths_and_build_space(level):
    grid = get_map(level)
    assert len(grid) == GRID_ROWS
    assert all(len(row) == GRID_COLS for row in grid)
    road = {(col, row) for row, cells in enumerate(grid)
            for col, value in enumerate(cells) if value in (1, 2, 3)}
    start = [(col, row) for col, row in road if grid[row][col] == 2]
    end = [(col, row) for col, row in road if grid[row][col] == 3]
    assert len(start) == len(end) == 1
    path = [(int(x // CELL_SIZE), int(y // CELL_SIZE)) for x, y in get_path(level)]
    assert path[0] == start[0]
    assert path[-1] == end[0]
    assert len(set(path)) == len(path) == len(road)
    for cell in road:
        x, y = cell
        neighbors = sum((x + dx, y + dy) in road for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)))
        assert neighbors == (1 if cell in start + end else 2)
        assert not is_buildable(x, y, level)
    assert sum(is_buildable(x, y, level) for y in range(GRID_ROWS) for x in range(GRID_COLS)) > 200
    assert all(0 <= x < GAME_WIDTH and 0 <= y < GAME_HEIGHT for x, y in get_path(level))
    grid[0][0] = 99
    assert get_map(level)[0][0] != 99  # Callers can't alter campaign maps.


@pytest.mark.parametrize("level", [5, 6, 7])
def test_enemies_reach_new_bases(level):
    path = get_path(level)
    enemy = Enemy("fast", path)
    for _ in range(len(path) * 50):
        enemy.update()
        if not enemy.alive:
            break
    assert enemy.reached_end


def test_old_progress_unlocks_new_maps_without_reset(tmp_path, monkeypatch):
    path = tmp_path / "highscores.json"
    original = {str(i): {"best_wave": 25, "best_kills": 200, "completed": True} for i in range(5)}
    path.write_text(json.dumps(original))
    monkeypatch.setattr(highscores, "HIGHSCORES_FILE", str(path))
    scores = HighscoreManager()
    assert scores.scores == original
    assert scores.is_level_unlocked(5)
    assert not scores.is_level_unlocked(6)
    scores.update_score(5, 25, 250, True)
    assert scores.is_level_unlocked(6)
    assert not scores.is_level_unlocked(7)
    assert HighscoreManager().get_score(5)["completed"]
    assert scores.get_score(4) == original["4"]


def test_new_campaign_size_and_localized_map_metadata(monkeypatch):
    assert len(LEVEL_DATA) == 8
    for language in ("ru", "en"):
        monkeypatch.setattr(config_manager, "language", language)
        for level in range(len(LEVEL_DATA)):
            info = get_level_info(level)
            assert 0 <= info["difficulty"] < 5
            assert info["name"] == LEVEL_DATA[level]["name_en" if language == "en" else "name"]
            assert "8" in t("subtitle").format(levels=len(LEVEL_DATA))


@pytest.mark.parametrize("language", ["ru", "en"])
def test_new_maps_render_and_carousel_wraps(game, monkeypatch, language):
    monkeypatch.setattr(config_manager, "language", language)
    for level in (5, 6, 7):
        game.current_level = level
        game.reset_game()
        game.start_wave()
        game.update_game(1000 / 60)
        game.draw_game()
        game.level_select_menu.selected_level = level
        game.level_select_menu.update((0, 0))
        game.level_select_menu.draw(game.screen)
    game.level_select_menu.next_level()
    assert game.level_select_menu.selected_level == 0
    game.level_select_menu.prev_level()
    assert game.level_select_menu.selected_level == len(LEVEL_DATA) - 1
    game.main_menu.draw(game.screen)
