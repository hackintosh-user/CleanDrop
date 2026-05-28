import sys
import platform
import subprocess
import customtkinter as ctk
import os
import shutil
import json
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk

# ─── macOS Version Check ────────────────────────────────────────────────────────

def check_macos_version():
    """Only allow macOS Sequoia 15.5 (build 24F74) and later."""
    if sys.platform != "darwin":
        _show_unsupported()

    ver = platform.mac_ver()[0]  # e.g. "15.5.0"
    try:
        parts = tuple(int(x) for x in ver.split("."))
    except ValueError:
        _show_unsupported()

    # Must be macOS 15.5+
    if parts < (15, 5):
        _show_unsupported()

    # If exactly 15.5, also check build number >= 24F74
    if parts == (15, 5):
        try:
            build = subprocess.check_output(
                ["sw_vers", "-buildVersion"], text=True
            ).strip()
            # Compare build strings: 24F74 — format is NNLnn (digits, letter, digits)
            # Simple lexicographic comparison works for same-prefix builds
            if build < "24F74":
                _show_unsupported()
        except Exception:
            _show_unsupported()

def _show_unsupported():
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Unsupported System",
        "Your System is unsupported, please update to macOS Sequoia 15.5 or later!"
    )
    root.destroy()
    sys.exit(1)

check_macos_version()

# ─── App Config ────────────────────────────────────────────────────────────────

APP_NAME = "CleanDrop"
VERSION  = "v1.0.0"

FILE_CATEGORIES = {
    "🖼  Images":    [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff", ".heic", ".raw"],
    "🎬  Videos":    [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".mpeg"],
    "🎵  Audio":     [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma", ".aiff"],
    "📄  Documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".rtf", ".odt", ".csv"],
    "📦  Archives":  [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".dmg", ".iso"],
    "💻  Apps":      [".exe", ".msi", ".pkg", ".app", ".deb", ".rpm", ".apk"],
    "💾  Code":      [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".sh", ".bat", ".java", ".cpp", ".c", ".go", ".rs"],
    "🗂  Other":     [],
}

HISTORY_FILE = Path.home() / ".cleandrop_history.json"

# ─── Theme ─────────────────────────────────────────────────────────────────────

DARK = {
    "bg":        "#0f1117",
    "surface":   "#1a1d27",
    "surface2":  "#22263a",
    "accent":    "#6c8fff",
    "accent2":   "#a78bfa",
    "success":   "#34d399",
    "warning":   "#fbbf24",
    "danger":    "#f87171",
    "text":      "#e2e8f0",
    "subtext":   "#64748b",
    "border":    "#2d3148",
}

LIGHT = {
    "bg":        "#f0f4ff",
    "surface":   "#ffffff",
    "surface2":  "#e8edf8",
    "accent":    "#4f6ef7",
    "accent2":   "#7c3aed",
    "success":   "#059669",
    "warning":   "#d97706",
    "danger":    "#dc2626",
    "text":      "#1e293b",
    "subtext":   "#64748b",
    "border":    "#cbd5e1",
}


# ─── Core Logic ────────────────────────────────────────────────────────────────

def get_category(filepath: Path) -> str:
    ext = filepath.suffix.lower()
    for cat, exts in FILE_CATEGORIES.items():
        if ext in exts:
            return cat
    return "🗂  Other"

def scan_folder(folder: Path) -> list[dict]:
    results = []
    for item in folder.iterdir():
        if item.is_file() and not item.name.startswith("."):
            cat  = get_category(item)
            size = item.stat().st_size
            results.append({
                "name":     item.name,
                "path":     str(item),
                "category": cat,
                "size":     size,
                "ext":      item.suffix.lower(),
            })
    return results

def human_size(b: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"

def save_history(moves: list[dict]):
    history = load_history()
    history.append({"timestamp": datetime.now().isoformat(), "moves": moves})
    history = history[-20:]  # keep last 20 sessions
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE) as f:
                return json.load(f)
        except Exception:
            return []
    return []

def do_clean(folder: Path, files: list[dict]) -> list[dict]:
    moves = []
    for f in files:
        src  = Path(f["path"])
        cat_name = f["category"].split("  ")[-1].strip()
        dest_dir = folder / cat_name
        dest_dir.mkdir(exist_ok=True)
        dest = dest_dir / src.name
        # avoid overwrite
        if dest.exists():
            stem, suffix = src.stem, src.suffix
            dest = dest_dir / f"{stem}_{datetime.now().strftime('%H%M%S')}{suffix}"
        shutil.move(str(src), str(dest))
        moves.append({"from": str(src), "to": str(dest)})
    save_history(moves)
    return moves

def undo_last_clean() -> tuple[bool, str]:
    history = load_history()
    if not history:
        return False, "No clean history found."
    last = history[-1]
    errors = []
    for move in reversed(last["moves"]):
        try:
            src = Path(move["to"])
            dst = Path(move["from"])
            if src.exists():
                shutil.move(str(src), str(dst))
        except Exception as e:
            errors.append(str(e))
    # remove last entry
    history.pop()
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    if errors:
        return False, f"Undone with {len(errors)} error(s)."
    return True, f"Restored {len(last['moves'])} file(s) from {last['timestamp'][:10]}."


# ─── GUI ───────────────────────────────────────────────────────────────────────

class CleanDrop(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.dark_mode   = True
        self.theme       = DARK
        self.folder_path = Path.home() / "Downloads"
        self.scanned     = []
        self.selected    = set()  # indices of checked files

        self.title(f"{APP_NAME} {VERSION}")
        self.geometry("920x680")
        self.minsize(800, 580)
        self.configure(fg_color=self.theme["bg"])

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._build_ui()
        self._apply_theme()

    # ── UI Build ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ──
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=64)
        self.header.pack(fill="x", padx=24, pady=(18, 0))
        self.header.pack_propagate(False)

        self.lbl_title = ctk.CTkLabel(
            self.header, text=f"✦ {APP_NAME}",
            font=ctk.CTkFont(family="Courier New", size=26, weight="bold"),
        )
        self.lbl_title.pack(side="left", pady=10)

        self.lbl_ver = ctk.CTkLabel(
            self.header, text=VERSION,
            font=ctk.CTkFont(size=11),
        )
        self.lbl_ver.pack(side="left", padx=(8, 0), pady=14)

        # right side header buttons
        self.btn_theme = ctk.CTkButton(
            self.header, text="☀  Light", width=90, height=32,
            corner_radius=8, command=self._toggle_theme,
            font=ctk.CTkFont(size=12),
        )
        self.btn_theme.pack(side="right", pady=10)

        self.btn_undo = ctk.CTkButton(
            self.header, text="↩  Undo", width=90, height=32,
            corner_radius=8, command=self._undo,
            font=ctk.CTkFont(size=12),
        )
        self.btn_undo.pack(side="right", padx=(0, 8), pady=10)

        # ── Folder picker ──
        self.folder_frame = ctk.CTkFrame(self, corner_radius=12, height=52)
        self.folder_frame.pack(fill="x", padx=24, pady=(14, 0))
        self.folder_frame.pack_propagate(False)

        self.lbl_folder = ctk.CTkLabel(
            self.folder_frame,
            text=f"📂  {self.folder_path}",
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self.lbl_folder.pack(side="left", padx=14, fill="x", expand=True)

        self.btn_browse = ctk.CTkButton(
            self.folder_frame, text="Browse", width=80, height=34,
            corner_radius=8, command=self._browse,
            font=ctk.CTkFont(size=12),
        )
        self.btn_browse.pack(side="right", padx=8)

        self.btn_scan = ctk.CTkButton(
            self.folder_frame, text="⟳  Scan", width=90, height=34,
            corner_radius=8, command=self._scan,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.btn_scan.pack(side="right", padx=(0, 4))

        # ── Stats bar ──
        self.stats_frame = ctk.CTkFrame(self, corner_radius=10, height=48)
        self.stats_frame.pack(fill="x", padx=24, pady=(10, 0))
        self.stats_frame.pack_propagate(False)

        self.lbl_stats = ctk.CTkLabel(
            self.stats_frame,
            text="Scan your Downloads folder to get started.",
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self.lbl_stats.pack(side="left", padx=14)

        self.lbl_selected = ctk.CTkLabel(
            self.stats_frame, text="",
            font=ctk.CTkFont(size=12),
            anchor="e",
        )
        self.lbl_selected.pack(side="right", padx=14)

        # ── Category filter ──
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.pack(fill="x", padx=24, pady=(10, 0))

        self.filter_var = ctk.StringVar(value="All")
        self.filter_btns: list[ctk.CTkButton] = []
        cats = ["All"] + [c.split("  ")[0] for c in FILE_CATEGORIES.keys()]
        for cat in cats:
            b = ctk.CTkButton(
                self.filter_frame, text=cat, width=52, height=28,
                corner_radius=6, command=lambda c=cat: self._filter(c),
                font=ctk.CTkFont(size=12),
            )
            b.pack(side="left", padx=(0, 6))
            self.filter_btns.append(b)

        # ── File list ──
        self.list_frame = ctk.CTkScrollableFrame(self, corner_radius=12)
        self.list_frame.pack(fill="both", expand=True, padx=24, pady=(10, 0))

        self.file_rows: list[dict] = []

        # ── Bottom bar ──
        self.bottom = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self.bottom.pack(fill="x", padx=24, pady=(10, 16))
        self.bottom.pack_propagate(False)

        self.btn_select_all = ctk.CTkButton(
            self.bottom, text="Select All", width=100, height=38,
            corner_radius=8, command=self._select_all,
            font=ctk.CTkFont(size=13),
        )
        self.btn_select_all.pack(side="left")

        self.btn_deselect = ctk.CTkButton(
            self.bottom, text="Deselect All", width=110, height=38,
            corner_radius=8, command=self._deselect_all,
            font=ctk.CTkFont(size=13),
        )
        self.btn_deselect.pack(side="left", padx=(8, 0))

        self.btn_clean = ctk.CTkButton(
            self.bottom, text="🧹  Clean Selected", width=180, height=38,
            corner_radius=8, command=self._confirm_clean,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.btn_clean.pack(side="right")

        self.lbl_status = ctk.CTkLabel(
            self.bottom, text="",
            font=ctk.CTkFont(size=12),
        )
        self.lbl_status.pack(side="right", padx=(0, 12))

    # ── Theme ──────────────────────────────────────────────────────────────────

    def _apply_theme(self):
        t = self.theme
        self.configure(fg_color=t["bg"])
        self.folder_frame.configure(fg_color=t["surface"], border_color=t["border"], border_width=1)
        self.stats_frame.configure(fg_color=t["surface2"])
        self.list_frame.configure(fg_color=t["surface"])

        self.lbl_title.configure(text_color=t["accent"])
        self.lbl_ver.configure(text_color=t["subtext"])
        self.lbl_folder.configure(text_color=t["text"])
        self.lbl_stats.configure(text_color=t["subtext"])
        self.lbl_selected.configure(text_color=t["accent"])
        self.lbl_status.configure(text_color=t["success"])

        self.btn_scan.configure(fg_color=t["accent"], hover_color=t["accent2"], text_color="#ffffff")
        self.btn_browse.configure(fg_color=t["surface2"], hover_color=t["border"], text_color=t["text"])
        self.btn_theme.configure(fg_color=t["surface2"], hover_color=t["border"], text_color=t["text"])
        self.btn_undo.configure(fg_color=t["surface2"], hover_color=t["border"], text_color=t["text"])
        self.btn_clean.configure(fg_color=t["success"], hover_color="#059669", text_color="#ffffff")
        self.btn_select_all.configure(fg_color=t["surface2"], hover_color=t["border"], text_color=t["text"])
        self.btn_deselect.configure(fg_color=t["surface2"], hover_color=t["border"], text_color=t["text"])

        for b in self.filter_btns:
            b.configure(fg_color=t["surface2"], hover_color=t["border"], text_color=t["text"])

        self._refresh_rows()

    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.theme = DARK if self.dark_mode else LIGHT
        ctk.set_appearance_mode("dark" if self.dark_mode else "light")
        self.btn_theme.configure(text="☀  Light" if self.dark_mode else "🌙  Dark")
        self._apply_theme()

    # ── Actions ────────────────────────────────────────────────────────────────

    def _browse(self):
        path = filedialog.askdirectory(initialdir=str(self.folder_path))
        if path:
            self.folder_path = Path(path)
            self.lbl_folder.configure(text=f"📂  {self.folder_path}")

    def _scan(self):
        self.lbl_status.configure(text="Scanning…")
        self.update()
        def run():
            self.scanned  = scan_folder(self.folder_path)
            self.selected = set(range(len(self.scanned)))
            self.after(0, self._on_scan_done)
        threading.Thread(target=run, daemon=True).start()

    def _on_scan_done(self):
        total_size = sum(f["size"] for f in self.scanned)
        cats = {}
        for f in self.scanned:
            cats[f["category"]] = cats.get(f["category"], 0) + 1
        cat_str = "  ·  ".join(f"{v} {k.split('  ')[0]}" for k, v in list(cats.items())[:4])
        self.lbl_stats.configure(
            text=f"{len(self.scanned)} files  ·  {human_size(total_size)}  ·  {cat_str}"
        )
        self.filter_var.set("All")
        self._build_rows(self.scanned)
        self._update_selected_label()
        self.lbl_status.configure(text="✓ Scan complete")

    def _build_rows(self, files: list[dict]):
        for w in self.list_frame.winfo_children():
            w.destroy()
        self.file_rows = []

        t = self.theme
        for i, f in enumerate(files):
            orig_idx = self.scanned.index(f)
            row = ctk.CTkFrame(self.list_frame, corner_radius=8, fg_color=t["surface2"], height=44)
            row.pack(fill="x", pady=(0, 4))
            row.pack_propagate(False)

            var = ctk.BooleanVar(value=(orig_idx in self.selected))
            cb = ctk.CTkCheckBox(
                row, text="", variable=var, width=24,
                command=lambda v=var, idx=orig_idx: self._on_check(v, idx),
                fg_color=t["accent"], hover_color=t["accent2"],
            )
            cb.pack(side="left", padx=(10, 4))

            lbl_cat = ctk.CTkLabel(
                row, text=f["category"].split("  ")[0], width=28,
                font=ctk.CTkFont(size=14),
            )
            lbl_cat.pack(side="left", padx=(0, 6))

            lbl_name = ctk.CTkLabel(
                row, text=f["name"], anchor="w",
                font=ctk.CTkFont(size=12),
                text_color=t["text"],
            )
            lbl_name.pack(side="left", fill="x", expand=True)

            lbl_dest = ctk.CTkLabel(
                row,
                text=f"→ {f['category'].split('  ')[-1].strip()}",
                font=ctk.CTkFont(size=11),
                text_color=t["subtext"],
            )
            lbl_dest.pack(side="right", padx=(0, 8))

            lbl_size = ctk.CTkLabel(
                row, text=human_size(f["size"]),
                font=ctk.CTkFont(size=11),
                text_color=t["subtext"], width=62,
            )
            lbl_size.pack(side="right")

            self.file_rows.append({"var": var, "orig_idx": orig_idx})

    def _refresh_rows(self):
        if self.scanned:
            self._build_rows(self.scanned)

    def _filter(self, cat: str):
        self.filter_var.set(cat)
        if cat == "All":
            filtered = self.scanned
        else:
            filtered = [f for f in self.scanned if f["category"].startswith(cat)]
        self._build_rows(filtered)

    def _on_check(self, var: ctk.BooleanVar, idx: int):
        if var.get():
            self.selected.add(idx)
        else:
            self.selected.discard(idx)
        self._update_selected_label()

    def _select_all(self):
        self.selected = set(range(len(self.scanned)))
        for row in self.file_rows:
            row["var"].set(True)
        self._update_selected_label()

    def _deselect_all(self):
        self.selected.clear()
        for row in self.file_rows:
            row["var"].set(False)
        self._update_selected_label()

    def _update_selected_label(self):
        n = len(self.selected)
        total_size = sum(self.scanned[i]["size"] for i in self.selected if i < len(self.scanned))
        self.lbl_selected.configure(
            text=f"{n} selected  ·  {human_size(total_size)}" if n else ""
        )

    def _confirm_clean(self):
        if not self.selected:
            messagebox.showwarning(APP_NAME, "No files selected.")
            return
        files = [self.scanned[i] for i in sorted(self.selected) if i < len(self.scanned)]
        total_size = human_size(sum(f["size"] for f in files))
        msg = (
            f"Move {len(files)} file(s) ({total_size}) into sorted subfolders?\n\n"
            f"You can undo this with the ↩ Undo button."
        )
        if messagebox.askyesno(f"{APP_NAME} — Confirm Clean", msg):
            self._run_clean(files)

    def _run_clean(self, files: list[dict]):
        self.btn_clean.configure(state="disabled", text="Cleaning…")
        self.lbl_status.configure(text="")
        def run():
            moves = do_clean(self.folder_path, files)
            self.after(0, lambda: self._on_clean_done(len(moves)))
        threading.Thread(target=run, daemon=True).start()

    def _on_clean_done(self, count: int):
        self.btn_clean.configure(state="normal", text="🧹  Clean Selected")
        self.lbl_status.configure(text=f"✓ Moved {count} file(s)")
        self._scan()

    def _undo(self):
        ok, msg = undo_last_clean()
        if ok:
            messagebox.showinfo(APP_NAME, msg)
            self._scan()
        else:
            messagebox.showwarning(APP_NAME, msg)


# ─── Entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = CleanDrop()
    app.mainloop()
