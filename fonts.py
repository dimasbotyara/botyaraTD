"""Bundled Cyrillic/Latin text with a monochrome emoji fallback (no OS fonts)."""

from functools import lru_cache
from pathlib import Path

import pygame

FONTS_DIR = Path(__file__).resolve().parent / "assets" / "fonts"


class GameFont:
    def __init__(self, size):
        # Match the visual size of Pygame's former built-in font, not its em size.
        pixel_size = max(1, round(size * 0.72))
        self.text_font = pygame.font.Font(str(FONTS_DIR / "NotoSans-Regular.ttf"), pixel_size)
        self.emoji_font = pygame.font.Font(str(FONTS_DIR / "NotoEmoji.ttf"), pixel_size)

    @lru_cache(maxsize=1024)
    def _font_for(self, char):
        if self.text_font.metrics(char)[0] is not None:
            return self.text_font
        return self.emoji_font

    def _runs(self, text):
        font = self.text_font
        run = ""
        for char in text:
            # The fallback is monochrome; presentation selectors aren't glyphs.
            if char in ("\ufe0e", "\ufe0f"):
                continue
            next_font = self._font_for(char)
            if next_font is not font and run:
                yield font, run
                run = ""
            font = next_font
            run += char
        if run:
            yield font, run

    def render(self, text, antialias, color, background=None):
        runs = [(font, font.render(run, antialias, color))
                for font, run in self._runs(text)]
        ascent = max((font.get_ascent() for font, _ in runs),
                     default=self.text_font.get_ascent())
        height = max((ascent - font.get_ascent() + image.get_height()
                      for font, image in runs), default=self.text_font.get_height())
        result = pygame.Surface((sum(image.get_width() for _, image in runs), height),
                                pygame.SRCALPHA)
        if background is not None:
            result.fill(background)
        x = 0
        for font, image in runs:
            result.blit(image, (x, ascent - font.get_ascent()))
            x += image.get_width()
        return result


@lru_cache(maxsize=64)
def get_font(size):
    """Share immutable font wrappers across menus and floating effects."""
    return GameFont(size)
