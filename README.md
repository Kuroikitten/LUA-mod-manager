# Lua Mod Manager

A simple, cross-platform mod manager for games that use Lua mods.

> ⚠️ **Vibe-coded.** This tool was built with AI assistance in a single session.

---

## Requirements

- Python 3.10+
- Tkinter (usually bundled with Python, see below if missing)

### Installing Tkinter on Linux

**Ubuntu / Debian**
```bash
sudo apt install python3-tk
```

**Fedora / RHEL**
```bash
sudo dnf install python3-tkinter
```

**Arch**
```bash
sudo pacman -S tk
```

On **Windows** and **macOS**, Tkinter ships with Python — no extra steps needed.

---

## Running

```bash
python mod_manager.py
# or
python3 mod_manager.py
```

On first launch you'll be asked to set a mods directory. This is saved to `~/.lua_mod_manager/config.json` and remembered between sessions.

---

## Features

- **Set mods directory** — point the manager at your game's mods folder
- **Install mod** — pick a `.zip` file, it gets extracted into the mods folder
- **Enable / Disable mod** — toggles `.disabled` on all Lua files in the mod's folder without deleting anything
- **Uninstall mod** — permanently removes the mod folder (asks for confirmation)
- **Mod list** — shows all detected mods and their current state

Buttons are context-sensitive: Enable and Disable only become clickable when they actually do something for the selected mod.

---

## Mod format

The manager expects mods to be distributed as `.zip` files containing a single top-level folder of Lua files:

```
my_mod.zip
└── my_mod/
    ├── main.lua
    └── utils.lua
```

When installed, that folder lands directly in your mods directory:

```
<mods_dir>/
└── my_mod/
    ├── main.lua
    └── utils.lua
```

When a mod is **disabled**, every `.lua` file gets renamed to `.lua.disabled`. Re-enabling reverses this. The mod folder itself is never touched.

---

## Config

Settings are stored in:

| Platform | Path |
|----------|------|
| Linux / macOS | `~/.lua_mod_manager/config.json` |
| Windows | `C:\Users\<you>\.lua_mod_manager\config.json` |

You can edit or delete this file manually if needed.

---

## License

Do whatever you want with it.
