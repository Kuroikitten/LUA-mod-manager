"""
Lua Mod Loader — cross-platform desktop app
Requires only Python 3.x stdlib (tkinter, zipfile, shutil, json, pathlib)
"""

import json
import shutil
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────
CONFIG_PATH = Path.home() / ".lua_mod_manager" / "config.json"
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return {"mods_dir": ""}

def save_config(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))

# ── Mod logic ─────────────────────────────────────────────────────────────────

def list_mods(mods_dir: Path) -> list[dict]:
    mods = []
    if not mods_dir.is_dir():
        return mods
    for entry in sorted(mods_dir.iterdir()):
        if not entry.is_dir():
            continue
        lua_files = list(entry.rglob("*.lua")) + list(entry.rglob("*.lua.disabled"))
        if not lua_files:
            continue
        disabled_count = sum(1 for f in lua_files if f.name.endswith(".disabled"))
        enabled = disabled_count < len(lua_files)
        mods.append({
            "name": entry.name,
            "path": entry,
            "enabled": enabled,
            "files": lua_files,
        })
    return mods


def install_mod(zip_path: Path, mods_dir: Path) -> str:
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        roots = {n.split("/")[0] for n in names if n.strip()}
        if len(roots) == 1:
            mod_name = roots.pop()
            dest = mods_dir / mod_name
            if dest.exists():
                raise FileExistsError(f'Mod "{mod_name}" is already installed.')
            z.extractall(mods_dir)
        else:
            mod_name = zip_path.stem
            dest = mods_dir / mod_name
            if dest.exists():
                raise FileExistsError(f'Mod "{mod_name}" is already installed.')
            dest.mkdir(parents=True, exist_ok=True)
            z.extractall(dest)
    return mod_name


def set_mod_enabled(mod: dict, enable: bool):
    for f in mod["path"].rglob("*"):
        if not f.is_file():
            continue
        if enable and f.name.endswith(".disabled"):
            f.rename(f.with_name(f.name[:-len(".disabled")]))
        elif not enable and f.suffix == ".lua":
            f.rename(f.with_name(f.name + ".disabled"))


def uninstall_mod(mod: dict):
    shutil.rmtree(mod["path"])


# ── Theme ─────────────────────────────────────────────────────────────────────

BG       = "#2b2b2b"
SURFACE  = "#333333"
BORDER   = "#444444"
TEXT     = "#d4d4d4"
TEXT_DIM = "#777777"
BTN_BG   = "#3c3c3c"
BTN_ACT  = "#505050"
GREEN    = "#6aaa6a"
FONT_B   = ("TkDefaultFont", 10)
FONT_S   = ("TkDefaultFont", 9)

# ── App ───────────────────────────────────────────────────────────────────────

class ModLoaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lua Mod Loader")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(640, 420)

        self.cfg = load_config()
        self._mod_map: dict[str, dict] = {}
        self._build_ui()
        self.refresh_mods()

        # Prompt for mods dir on first launch
        if not self.cfg.get("mods_dir", "").strip():
            self.after(100, self._prompt_mods_dir)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Directory bar
        dir_frame = tk.Frame(self, bg=BG, padx=10, pady=8)
        dir_frame.grid(row=0, column=0, sticky="ew")
        dir_frame.columnconfigure(1, weight=1)

        tk.Label(dir_frame, text="Mods directory:", font=FONT_S,
                 bg=BG, fg=TEXT_DIM).grid(row=0, column=0, padx=(0, 6))

        self.dir_var = tk.StringVar(value=self.cfg.get("mods_dir", ""))
        tk.Entry(dir_frame, textvariable=self.dir_var, font=FONT_S,
                 bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                 relief="flat", highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor="#666666"
                 ).grid(row=0, column=1, sticky="ew", ipady=4, padx=(0, 6))

        self._btn(dir_frame, "Browse", self.browse_dir
                  ).grid(row=0, column=2, padx=(0, 4))
        self._btn(dir_frame, "Apply", self.apply_dir
                  ).grid(row=0, column=3)

        # Separator
        tk.Frame(self, bg=BORDER, height=1).grid(row=0, column=0,
                                                  sticky="sew")

        # Mod list
        list_frame = tk.Frame(self, bg=SURFACE)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(8, 4))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Treeview",
                        background=SURFACE, foreground=TEXT,
                        fieldbackground=SURFACE, rowheight=26,
                        font=FONT_B, borderwidth=0, relief="flat")
        style.configure("Treeview.Heading",
                        background=BTN_BG, foreground=TEXT_DIM,
                        font=FONT_S, relief="flat")
        style.map("Treeview",
                  background=[("selected", BTN_ACT)],
                  foreground=[("selected", TEXT)])

        self.tree = ttk.Treeview(list_frame, columns=("name", "status"),
                                 show="headings", selectmode="browse")
        self.tree.heading("name",   text="Mod name")
        self.tree.heading("status", text="Status")
        self.tree.column("name",   anchor="w", stretch=True)
        self.tree.column("status", anchor="center", width=100, stretch=False)
        self.tree.bind("<<TreeviewSelect>>", lambda _: self._update_buttons())

        vsb = ttk.Scrollbar(list_frame, orient="vertical",
                             command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # Toolbar
        toolbar = tk.Frame(self, bg=BG, padx=10, pady=8)
        toolbar.grid(row=2, column=0, sticky="ew")

        self.btn_install   = self._btn(toolbar, "Install mod",  self.install_mod)
        self.btn_enable    = self._btn(toolbar, "Enable",        self.enable_mod)
        self.btn_disable   = self._btn(toolbar, "Disable",       self.disable_mod)
        self.btn_uninstall = self._btn(toolbar, "Uninstall",     self.uninstall_mod)
        self.btn_refresh   = self._btn(toolbar, "Refresh",       self.refresh_mods)

        self.btn_install.pack(side="left", padx=(0, 4))
        self.btn_enable.pack(side="left", padx=(0, 4))
        self.btn_disable.pack(side="left", padx=(0, 4))
        self.btn_uninstall.pack(side="left")
        self.btn_refresh.pack(side="right")

        # Status bar
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(self, textvariable=self.status_var, font=FONT_S,
                 bg=BG, fg=TEXT_DIM, anchor="w", padx=10, pady=4
                 ).grid(row=3, column=0, sticky="ew")

        self._update_buttons()

    def _btn(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd,
                         font=FONT_S, bg=BTN_BG, fg=TEXT,
                         activebackground=BTN_ACT, activeforeground=TEXT,
                         relief="flat", padx=10, pady=4,
                         cursor="hand2", bd=0,
                         disabledforeground=TEXT_DIM)

    # ── Button state management ───────────────────────────────────────────────

    def _update_buttons(self):
        sel = self.tree.selection()
        mod = self._mod_map.get(sel[0]) if sel else None

        if mod is None:
            self.btn_enable.config(state="disabled")
            self.btn_disable.config(state="disabled")
            self.btn_uninstall.config(state="disabled")
        else:
            self.btn_uninstall.config(state="normal")
            if mod["enabled"]:
                self.btn_enable.config(state="disabled")
                self.btn_disable.config(state="normal")
            else:
                self.btn_enable.config(state="normal")
                self.btn_disable.config(state="disabled")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _prompt_mods_dir(self):
        if messagebox.askyesno(
                "Mods directory not set",
                "No mods directory is configured.\nWould you like to choose one now?"):
            self.browse_dir()

    def browse_dir(self):
        d = filedialog.askdirectory(title="Select mods directory")
        if d:
            self.dir_var.set(d)
            self.apply_dir()

    def apply_dir(self):
        d = self.dir_var.get().strip()
        if not d:
            return
        path = Path(d)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot use directory:\n{e}")
            return
        self.cfg["mods_dir"] = str(path)
        save_config(self.cfg)
        self.refresh_mods()
        self.status("Mods directory set.")

    def _mods_dir(self) -> Path | None:
        d = self.cfg.get("mods_dir", "").strip()
        if not d:
            messagebox.showwarning("No mods directory",
                                   "Please set a mods directory first.")
            return None
        return Path(d)

    def install_mod(self):
        mods_dir = self._mods_dir()
        if not mods_dir:
            return
        zip_path = filedialog.askopenfilename(
            title="Select mod zip",
            filetypes=[("Zip archives", "*.zip"), ("All files", "*.*")])
        if not zip_path:
            return
        try:
            name = install_mod(Path(zip_path), mods_dir)
            self.refresh_mods()
            self.status(f'"{name}" installed.')
        except FileExistsError as e:
            messagebox.showerror("Already installed", str(e))
        except Exception as e:
            messagebox.showerror("Install failed", str(e))

    def _selected_mod(self) -> dict | None:
        sel = self.tree.selection()
        return self._mod_map.get(sel[0]) if sel else None

    def enable_mod(self):
        mod = self._selected_mod()
        if not mod:
            return
        try:
            set_mod_enabled(mod, True)
            self.refresh_mods()
            self.status(f'"{mod["name"]}" enabled.')
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def disable_mod(self):
        mod = self._selected_mod()
        if not mod:
            return
        try:
            set_mod_enabled(mod, False)
            self.refresh_mods()
            self.status(f'"{mod["name"]}" disabled.')
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def uninstall_mod(self):
        mod = self._selected_mod()
        if not mod:
            return
        if not messagebox.askyesno("Confirm",
                                    f'Remove "{mod["name"]}" permanently?'):
            return
        try:
            uninstall_mod(mod)
            self.refresh_mods()
            self.status(f'"{mod["name"]}" uninstalled.')
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_mods(self):
        # Preserve selection across refresh
        sel_name = None
        sel = self.tree.selection()
        if sel:
            old = self._mod_map.get(sel[0])
            if old:
                sel_name = old["name"]

        self._mod_map = {}
        for row in self.tree.get_children():
            self.tree.delete(row)

        mods_dir = Path(self.cfg.get("mods_dir", ""))
        mods = list_mods(mods_dir) if mods_dir.is_dir() else []

        restore_iid = None
        for mod in mods:
            status_text = "enabled" if mod["enabled"] else "disabled"
            iid = self.tree.insert("", "end",
                                   values=(mod["name"], status_text),
                                   tags=("on" if mod["enabled"] else "off",))
            self._mod_map[iid] = mod
            if mod["name"] == sel_name:
                restore_iid = iid

        self.tree.tag_configure("on",  foreground=GREEN)
        self.tree.tag_configure("off", foreground=TEXT_DIM)

        if restore_iid:
            self.tree.selection_set(restore_iid)
            self.tree.see(restore_iid)

        count = len(mods)
        self.status(f"{count} mod{'s' if count != 1 else ''} found."
                    if count else "No mods found.")
        self._update_buttons()

    def status(self, msg: str):
        self.status_var.set(msg)


if __name__ == "__main__":
    app = ModLoaderApp()
    app.mainloop()
