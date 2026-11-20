# Bundled fonts

These fonts are distributed with the game so that Cyrillic text and emoji work
without system fonts or an internet connection. Emoji are **monochrome**, tinted
with the text color, not platform-specific color emoji.

Downloaded on 2026-11-20:

- `NotoSans-Regular.ttf` — Noto Sans Regular (Latin and Cyrillic).
  Source: https://github.com/notofonts/noto-fonts/blob/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf
  License: `NotoSans-LICENSE.txt` (SIL Open Font License 1.1).
- `NotoEmoji.ttf` — Noto Emoji, variable weight font (default weight).
  Source: https://github.com/google/fonts/blob/main/ofl/notoemoji/NotoEmoji%5Bwght%5D.ttf
  License: `NotoEmoji-OFL.txt` (SIL Open Font License 1.1).

Both files are unmodified upstream fonts. `fonts.py` caches font instances and
selects the emoji fallback for characters not covered by Noto Sans. Asset paths
are relative to the module, not the process's current directory. The supported
fallback covers the game's emoji and many others; it is not a full Unicode font
or a general-purpose complex emoji sequence renderer. Ability icons are drawn
with `icons.py` rather than font glyphs.
