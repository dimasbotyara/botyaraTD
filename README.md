# 🏰 botyaraTD

> **A juicy, feature-packed Tower Defense built with Pygame.** 5 levels, 8 tower types, 10 enemy types, super abilities, and enough particles to make your GPU sweat.

A complete tower defense game with a campaign, upgradeable towers, super abilities, progressive waves, and a slick UI — all in pure Pygame, no external engine.

---

## ✨ Features

### 🎯 Campaign — 5 Unique Levels
Each level has its own hand-crafted map, palette, and atmosphere:

| # | Level | Difficulty | Vibe |
|---|-------|-----------|------|
| 1 | 🌿 Green Meadow | Easy | Cozy valley — perfect for learning |
| 2 | 🏜️ Sand Canyon | Normal | Spiral desert paths, long walks |
| 3 | ❄️ Ice Peak | Hard | Frozen pass, freeze towers shine |
| 4 | 🌃 Neon City | Expert | Cyberpunk grid, fast attackers |
| 5 | 🌋 Volcano of Death | Apocalypse | Lava citadel, boss rushes |

Levels unlock progressively — complete one to unlock the next. Beat all 5 to win the campaign.

### 🗼 8 Tower Types × 3 Upgrade Levels
Every tower has three tiers, and each tier changes its **damage, fire rate, range, and special effects**:

- 🔫 **Machine Gun** — fast, cheap, reliable
- 🎯 **Sniper** — long range, massive single-target damage
- ❄️ **Freeze** — slows enemies in a radius
- 💣 **Cannon** — splash damage AOE
- 🔴 **Laser** — continuous beam, melts single targets
- ☠️ **Poison** — damage-over-time, stacks
- ⚡ **Tesla** — chain lightning, hits up to 5 enemies
- 🚀 **Missile** — homing projectiles with splash

Towers **recoil** when firing, have unique vector graphics, and show level stars.

### 💥 Super Abilities
Three cooldown-based abilities with bright vector icons:

| Key | Ability | Cost | Cooldown | Effect |
|-----|---------|------|----------|--------|
| `Q` | 💣 Airstrike | 100g | 45s | Massive damage along the whole path + screen shake |
| `W` | ❄️ Cryo Freeze | 50g | 30s | Slows all enemies on screen for 5 seconds |
| `E` | 💰 Gold Rush | free | 40s | +150 gold instantly |

### 👾 10 Enemy Types
Each with unique behavior:

- 🟢 **Soldier** — basic grunt
- 🟡 **Runner** — fast, fragile
- 🔴 **Tank** — high HP, slow
- 💗 **Medic** — heals nearby enemies
- 🔵 **Shieldbearer** — has a regenerating shield
- 🟠 **Swarm** — tiny, spawns in huge groups
- 👻 **Ghost** — periodically becomes invisible, dodges attacks
- 🟠 **Splitter** — splits into smaller swarm units on death
- 🟣 **Boss** — massive HP, huge reward
- 🔴 **Mega Boss** — the final nightmare

### 🌊 25 Waves with Progressive Difficulty
Hand-tuned wave compositions — from a gentle tutorial opener to a final wave with 40+ enemies including two Mega Bosses. Mini-bosses appear at waves 5, 10, 15, 20, and 25.

### 🎮 5 Difficulty Levels
Chosen in settings:
- **Easy** — more gold, fewer enemies
- **Normal** — balanced
- **Hard** — less gold, stronger enemies

Affects enemy HP, rewards, wave size, and difficulty scaling.

### 🎨 Juicy Visual Effects
All in `effects.py`, easy to tweak:

- 💥 **Particle explosions** on enemy death (color-matched to enemy)
- 🌊 **Shockwave rings** for AOE damage
- 💬 **Floating damage numbers** and gold popups
- ⚡ **Lightning bolts** for Tesla tower (procedurally jittered)
- 🔫 **Laser beams** with glow
- 📳 **Screen shake** for explosions, airstrikes, and enemy leaks
- ✨ **Pulsing UI elements**, tower recoil, muzzle flashes

### 🔊 Hybrid Sound System
- **Procedurally synthesized** sounds for the machine gun, gold pickup, and airstrike (generated on-the-fly with `array`)
- **External audio support** — drop `.wav` / `.mp3` / `.ogg` files into `sounds/` with names like `sniper.wav`, `explosion.mp3`, `victory.ogg` and they'll be auto-loaded
- Volume control in settings (0–100% in 25% steps)

### 🌍 Bilingual (RU / EN)
Full interface translation, switchable in settings, saved to `config.json`.

### 💾 Persistent Progress
- `config.json` — language, volume, difficulty
- `highscores.json` — best wave, best kills, completion status per level
- Level unlocking tied to completion

### 🖥️ Extra Conveniences
- 🏆 **Star ratings** per level (1–3 stars based on progress)
- 🎬 **Animated main menu** with drifting particles
- 🔒 **Lock screen** for unplayed levels
- 🎥 **In-world tower menu** — click any placed tower to upgrade or sell
- ⏩ **Game speed toggle** (×1 / ×3)
- ⌨️ **Full keyboard support** — 1-8 for towers, Q/W/E abilities, ESC pause
- 🪟 **F9 hides window** (Windows via `ctypes`, Linux via `pygame.iconify`)
- 🖱️ **Right-click to deselect** towers

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/dimasbotyara/botyaraTD.git
cd botyaraTD

# 2. (Optional) Virtual environment
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

Or use the launch scripts — `run.sh` (Linux/macOS), `run.bat` (Windows CMD), or `run.ps1` (PowerShell).

**Requires:** Python 3.9+ and `pygame >= 2.1`.

---

## 🎮 Controls

| Input | Action |
|-------|--------|
| **Click** on map | Place tower / select tower |
| **Right-click** | Deselect tower |
| **`1`–`8`** | Select tower type |
| **`Q` / `W` / `E`** | Trigger abilities (airstrike / freeze / gold) |
| **`Space`** | Start next wave |
| **`ESC`** | Pause / back |
| **`F9`** | Hide / show window |
| **Click placed tower** | Open upgrade / sell menu |
| **Sidebar buttons** | Everything above, plus speed toggle |

---

## 📁 Project Structure

```
botyaraTD/
├── main.py              # 🎯 Game class, main loop, state machine
├── settings.py          # Constants, tower/enemy stats, colors, balance
├── map_data.py          # 5 hand-crafted levels, path auto-generation
├── tower.py             # Tower classes, targeting, shooting, recoil
├── enemy.py             # Enemy classes, status effects, special behaviors
├── projectile.py        # Bullets, missiles, sniper shots, splash logic
├── wave.py              # Wave compositions (25 waves, hand-tuned)
├── effects.py           # Particles, shockwaves, beams, screen shake
├── ui.py                # All menus, sidebar, level select, in-world menus
├── icons.py             # Vector icons (bomb, ice, gold, trophy, lock, star)
├── sound.py             # Procedural + external sound manager
├── config.py            # Settings persistence (RU/EN translations)
├── highscores.py        # Progress & record persistence
├── run.sh / .bat / .ps1 # Convenience launch scripts
├── sounds/              # Drop your own .wav/.mp3/.ogg here
└── requirements.txt
```

---

## 🔧 Customization

Everything balance-related lives in **`settings.py`**:

```python
START_GOLD = 250          # Starting money
START_LIVES = 25          # Starting HP
MAX_WAVES = 25            # Waves per game
SELL_RATIO = 0.6          # Refund percentage

TOWER_STATS = { ... }     # Damage, range, cost, special effects per level
ENEMY_STATS = { ... }     # HP, speed, reward, special traits
```

Wave compositions live in **`wave.py`** — edit `get_wave(n)` to change any wave.

Levels live in **`map_data.py`** — edit the `grid` arrays or add a new `LEVEL_DATA` entry.

Custom sounds: drop a file named after the tower/event into `sounds/`. No code changes needed. See `sounds/license.txt` for licensing of bundled assets.

---

## 🛠️ Tech Stack

- 🐍 **Python 3.9+**
- 🎮 **Pygame** — rendering, input, sound
- 📦 **array** — procedural audio buffer generation
- 🔢 **Pure Python** — no numpy, no external game engine

---

## 📜 License

MIT — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**dimasbotyara** — [@dimasbotyara](https://github.com/dimasbotyara)

Made with 🔥 and too many `pygame.draw.circle` calls.

---

<div align="center">

**If you had fun, drop a ⭐**

</div>
