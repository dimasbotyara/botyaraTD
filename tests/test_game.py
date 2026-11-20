import json
from unittest.mock import Mock

import pygame
import pytest

import config
import enemy as enemy_module
import effects
import sound
from config import TRANSLATIONS, ConfigManager, config_manager, t
from effects import FloatingText
from enemy import Enemy
from fonts import get_font
from settings import DIFFICULTY_MODIFIERS, ENEMY_STATS, FPS, MAX_WAVES
from ui import SettingsMenu
from wave import get_wave


@pytest.mark.parametrize("difficulty", range(5))
def test_all_difficulties_affect_waves_enemies_and_bonus(game, difficulty):
    config_manager.difficulty = difficulty
    modifiers = DIFFICULTY_MODIFIERS[difficulty]
    game.wave_num = 9
    game.start_wave()
    original = get_wave(10)
    assert len(game.wave_queue) == int(len(original) * modifiers["enemy_count"])
    assert game.wave_queue[:3] == original[:3]

    game.spawn_enemy("basic")
    spawned = game.enemies[0]
    scale = 1 + (int(10 * modifiers["wave_scale"]) - 1) * 0.12
    assert spawned.hp == pytest.approx(ENEMY_STATS["basic"]["hp"] * scale * modifiers["hp"])
    assert spawned.max_hp == spawned.hp
    assert spawned.reward == int(ENEMY_STATS["basic"]["reward"] * modifiers["reward"])

    game.wave_queue.clear()
    game.enemies.clear()
    gold = game.gold
    game._game_tick()
    bonus = int((15 + 10 * 3) * modifiers["wave_bonus"])
    assert game.gold == gold + bonus
    assert not game.wave_active
    assert game.effects.floating_texts[-1].text == t("wave_cleared").format(wave=10, bonus=bonus)
    game._game_tick()
    assert game.gold == gold + bonus  # No repeated wave reward.


def test_difficulty_menu_cycles_all_five():
    config_manager.difficulty = 0
    menu = SettingsMenu()
    for expected in (1, 2, 3, 4, 0):
        menu.toggle_difficulty()
        assert config_manager.difficulty == expected


@pytest.mark.parametrize("difficulty", [-1, 5, 999])
def test_unknown_saved_difficulty_falls_back_to_normal(tmp_path, monkeypatch, difficulty):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"difficulty": difficulty}))
    monkeypatch.setattr(config, "CONFIG_FILE", str(path))
    assert ConfigManager().difficulty == 1


@pytest.mark.parametrize("speed", [1, 3])
@pytest.mark.parametrize("frame_ms", [1000 / 30, 1000 / 60, 1000 / 144])
def test_cooldowns_follow_elapsed_game_time(game, monkeypatch, speed, frame_ms):
    # Keep the wave active, independent of its composition or length.
    tick = Mock()
    monkeypatch.setattr(game, "_game_tick", tick)
    game.wave_active = True
    game.game_speed = speed
    game.cd_airstrike = 45_000
    game.cd_freeze = 30_000
    game.cd_gold = 40_000
    frames = round(1000 / frame_ms)
    for _ in range(frames):
        game.update_game(frame_ms)
    assert game.cd_airstrike == pytest.approx(45_000 - 1000 * speed)
    assert game.cd_freeze == pytest.approx(30_000 - 1000 * speed)
    assert game.cd_gold == pytest.approx(40_000 - 1000 * speed)
    assert tick.call_count == FPS * speed


@pytest.mark.parametrize("state,active", [("playing", False), ("paused", True), ("menu", True), ("game_over", True)])
def test_cooldowns_and_abilities_do_not_run_outside_waves(game, state, active):
    game.state = state
    game.wave_active = active
    game.cd_airstrike = 5000
    game.cd_freeze = 5000
    game.cd_gold = 5000
    game.update_game(1000)
    assert (game.cd_airstrike, game.cd_freeze, game.cd_gold) == (5000, 5000, 5000)
    game.cd_airstrike = game.cd_freeze = game.cd_gold = 0
    gold = game.gold
    for ability in ("airstrike", "freeze", "gold"):
        game.trigger_ability(ability)
    assert game.gold == gold
    assert (game.cd_airstrike, game.cd_freeze, game.cd_gold) == (0, 0, 0)


def test_cooldowns_clamp_at_zero(game, monkeypatch):
    monkeypatch.setattr(game, "_game_tick", lambda: None)
    game.wave_active = True
    game.cd_airstrike = game.cd_freeze = game.cd_gold = 1
    game.update_game(50)
    assert (game.cd_airstrike, game.cd_freeze, game.cd_gold) == (0, 0, 0)


@pytest.mark.parametrize("fps", [30, 60, 120])
def test_poison_uses_configured_simulation_rate(monkeypatch, fps):
    monkeypatch.setattr(enemy_module, "FPS", fps)
    poisoned = Enemy("tank", [(0, 0), (100000, 0)])
    initial_hp = poisoned.hp
    poisoned.apply_poison(6, fps * 2)
    for _ in range(fps * 2):
        poisoned.update()
    assert initial_hp - poisoned.hp == pytest.approx(12)
    poisoned.update()
    assert initial_hp - poisoned.hp == pytest.approx(12)
    assert not poisoned.is_poisoned_visual


@pytest.mark.parametrize("speed", [1, 3])
@pytest.mark.parametrize("frame_rate", [30, 60, 144])
def test_poison_total_damage_is_same_at_each_speed_and_frame_rate(game, speed, frame_rate):
    poisoned = Enemy("tank", [(0, 0), (100000, 0)])
    poisoned.apply_poison(6, FPS * 2)
    initial_hp = poisoned.hp
    game.enemies = [poisoned]
    game.wave_active = True
    game.game_speed = speed
    for _ in range(frame_rate * 2):
        game.update_game(1000 / frame_rate)
    assert initial_hp - poisoned.hp == pytest.approx(12)


@pytest.mark.parametrize("language", ["ru", "en"])
def test_ability_popups_have_translated_text_and_vector_icons(game, language):
    config_manager.language = language
    game.wave_active = True
    game.gold = 1000
    for ability, translation_key, cooldown in (
        ("airstrike", "airstrike_used", 45_000),
        ("freeze", "freeze_used", 30_000),
        ("gold", "gold_used", 40_000),
    ):
        game.trigger_ability(ability)
        popup = game.effects.floating_texts[-1]
        assert popup.text == t(translation_key)
        assert popup.icon == ability
        assert getattr(game, f"cd_{ability}") == cooldown
        popup.draw(game.screen)
        gold = game.gold
        game.trigger_ability(ability)
        assert game.gold == gold


def test_translations_are_complete_and_have_no_placeholder_prefixes():
    assert TRANSLATIONS["ru"].keys() == TRANSLATIONS["en"].keys()
    for translations in TRANSLATIONS.values():
        for value in translations.values():
            assert not any(prefix in value for prefix in ("[BOMB]", "[ICE]", "[GOLD]"))


def test_fonts_are_offline_and_cwd_independent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    font = get_font(37)  # Use a size not yet cached.
    assert font.text_font.metrics("Ж")[0] is not None
    missing = font.emoji_font.render("\uffff", True, "white")
    missing_pixels = pygame.image.tobytes(missing, "RGBA")
    for emoji in "😁🏆🔒💡🌿🌃🌋":
        assert font._font_for(emoji) is font.emoji_font
        image = font.render(emoji, True, "white")
        assert image.get_bounding_rect().width > 0
        assert pygame.image.tobytes(image, "RGBA") != missing_pixels
    for translations in TRANSLATIONS.values():
        for text in translations.values():
            assert font.render(text, True, "white").get_height() > 0
    assert get_font(37) is font


def test_floating_text_draws_requested_icon(monkeypatch):
    draw_icon = Mock()
    monkeypatch.setitem(effects.ABILITY_ICONS, "gold", draw_icon)
    popup = FloatingText(100, 100, "Золото!", (255, 215, 0), icon="gold")
    popup.draw(pygame.Surface((400, 200)))
    draw_icon.assert_called_once()


def test_missing_sounds_are_logged_once_not_on_play(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(sound, "SOUNDS_DIR", tmp_path)
    manager = sound.SoundManager()
    warnings = [record for record in caplog.records if record.name == "sound"]
    assert len(warnings) == 1
    assert "sniper" in warnings[0].message
    assert "victory" in warnings[0].message
    assert manager.sounds["sniper"] is None
    for _ in range(5):
        manager.play("sniper")
    assert len([record for record in caplog.records if record.name == "sound"]) == 1


def test_external_sound_still_loads(tmp_path, monkeypatch, caplog):
    path = tmp_path / "sniper.wav"
    path.touch()
    external = Mock()
    monkeypatch.setattr(sound, "SOUNDS_DIR", tmp_path)
    monkeypatch.setattr(pygame.mixer, "Sound", lambda *args, **kwargs: external)
    channel = Mock()
    channel.get_busy.return_value = False
    monkeypatch.setattr(pygame.mixer, "Channel", lambda index: channel)
    manager = sound.SoundManager()
    manager.play("sniper")
    channel.play.assert_called_once_with(external)
    assert "sniper" not in caplog.records[-1].message


def test_final_wave_stops_simulation_after_game_over(game, monkeypatch):
    game.wave_num = MAX_WAVES
    game.wave_active = True
    tick = Mock(wraps=game._game_tick)
    monkeypatch.setattr(game, "_game_tick", tick)
    game.update_game(1000)
    assert game.state == "game_over"
    assert game.game_won
    assert tick.call_count == 1
