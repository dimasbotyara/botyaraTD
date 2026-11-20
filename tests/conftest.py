import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame
import pytest

from config import config_manager
from fonts import get_font
from highscores import highscore_manager
from main import Game


@pytest.fixture(scope="session", autouse=True)
def pygame_session():
    pygame.init()
    yield
    get_font.cache_clear()
    pygame.quit()


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch):
    monkeypatch.setattr(config_manager, "difficulty", 1)
    monkeypatch.setattr(config_manager, "language", "ru")
    monkeypatch.setattr(config_manager, "save_config", lambda: None)
    monkeypatch.setattr(highscore_manager, "update_score", lambda *args: None)


@pytest.fixture
def game():
    result = Game()
    result.state = "playing"
    return result
