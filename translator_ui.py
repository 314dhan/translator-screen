# -*- coding: utf-8 -*-
"""
Translator Screen — region-select UI.

Click "Capture Region" (or press Space), drag to select any area on screen,
then see the detected text and translation in this panel.
"""
import ctypes
import ctypes.wintypes
import threading
import time
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

# Transparency
OPACITY_DEFAULT = 0.88        # initial window alpha
ACRYLIC_TINT    = 0x80000000  # ARGB semi-transparent black tint

# Global hotkey (Ctrl+Space)
_MOD_CTRL  = 0x0002
_VK_SPACE  = 0x20
_WM_HOTKEY = 0x0312
_HK_ID     = 1

class _ACCENTPOLICY(ctypes.Structure):
    _fields_ = [("AccentState", ctypes.c_uint), ("AccentFlags", ctypes.c_uint),
                ("GradientColor", ctypes.c_uint), ("AnimationId", ctypes.c_uint)]

class _WCAD(ctypes.Structure):
    _fields_ = [("Attribute", ctypes.c_int), ("Data", ctypes.c_void_p),
                ("SizeOfData", ctypes.c_size_t)]

def _apply_acrylic(hwnd: int, tint: int) -> None:
    accent = _ACCENTPOLICY(AccentState=4, AccentFlags=2, GradientColor=tint)
    data   = _WCAD(Attribute=19,
                   Data=ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p),
                   SizeOfData=ctypes.sizeof(accent))
    ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))

BG     = "#0f0f1a"
BG2    = "#1a1a2e"
BG3    = "#16213e"
ACCENT = "#4ecca3"
ACC2   = "#e94560"
GOLD   = "#f0c040"
TEXT   = "#dde1e7"
DIM    = "#6c7a8d"
WHITE  = "#ffffff"

LANGS = [
    ("English",     "en"),
    ("Indonesian",  "id"),
    ("Japanese",    "ja"),
    ("Korean",      "ko"),
    ("Chinese (S)", "zh-CN"),
    ("Chinese (T)", "zh-TW"),
    ("French",      "fr"),
    ("German",      "de"),
    ("Spanish",     "es"),
    ("Arabic",      "ar"),
    ("Russian",     "ru"),
    ("Hindi",       "hi"),
    ("Portuguese",  "pt"),
    ("Vietnamese",  "vi"),
    ("Thai",        "th"),
]
LANG_NAMES = [n for n, _ in LANGS]
LANG_CODE  = {n: c for n, c in LANGS}

SOURCE_LANGS = [("Auto Detect", "auto")] + LANGS
SRC_NAMES    = [n for n, _ in SOURCE_LANGS]
SRC_CODE     = {n: c for n, c in SOURCE_LANGS}


class TranslatorUI:

    WIN_W = 760
    WIN_H = 780

    def __init__(self, processor):
        self._proc          = processor
        self._busy          = False
        self._preview_photo = None
        self._quit_flag     = False

        self._build_root()
        self._build_ui()
        self._setup_hotkey()

    # ------------------------------------------------------------------
    # Window construction
    # ------------------------------------------------------------------

    def _build_root(self):
        self.root = tk.Tk()
        self.root.title("Translator Screen")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(520, 460)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x  = (sw - self.WIN_W) // 2
        y  = (sh - self.WIN_H) // 2
        self.root.geometry(f"{self.WIN_W}x{self.WIN_H}+{x}+{y}")
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

        self.root.wm_attributes("-toolwindow", True)  # hide from taskbar
        self.root.update()
        try:
            _apply_acrylic(self.root.winfo_id(), ACRYLIC_TINT)
        except Exception:
            pass  # Windows 10 / VM fallback — plain alpha still applies
        self.root.wm_attributes("-alpha", OPACITY_DEFAULT)

    def _build_ui(self):
        self._build_topbar()
        self._build_capture_row()
        self._build_body()
        self._build_statusbar()

    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=BG3, height=50)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(
            bar, text="  Translator Screen",
            bg=BG3, fg=ACCENT, font=("Segoe UI", 13, "bold"),
        ).pack(side="left", pady=6)

        self._pinned = tk.BooleanVar(value=True)
        tk.Checkbutton(
            bar, text="Pin",
            variable=self._pinned,
            command=self._toggle_pin,
            bg=BG3, fg=DIM, selectcolor=BG3,
            activebackground=BG3, activeforeground=ACCENT,
            font=("Segoe UI", 9),
        ).pack(side="right", padx=(0, 8))
        self.root.wm_attributes("-topmost", True)

        # Opacity slider
        tk.Label(bar, text="Opacity:", bg=BG3, fg=DIM,
                 font=("Segoe UI", 9)).pack(side="right", padx=(0, 2))
        self._opacity_var = tk.DoubleVar(value=OPACITY_DEFAULT)
        ttk.Scale(bar, from_=0.3, to=1.0, orient="horizontal", length=80,
                  variable=self._opacity_var,
                  command=lambda v: self.root.wm_attributes("-alpha", float(v)),
                  ).pack(side="right", padx=(0, 6), pady=10)

        # Target language
        tk.Label(bar, text="→ Target:", bg=BG3, fg=DIM,
                 font=("Segoe UI", 9)).pack(side="right", padx=(0, 2))

        self._target_var = tk.StringVar(value="Indonesian")
        target_cb = ttk.Combobox(
            bar, textvariable=self._target_var,
            values=LANG_NAMES, width=12, state="readonly",
            font=("Segoe UI", 9),
        )
        target_cb.pack(side="right", padx=(0, 6), pady=8)
        target_cb.bind("<<ComboboxSelected>>", self._on_target_lang)

        # Source language
        tk.Label(bar, text="Source:", bg=BG3, fg=DIM,
                 font=("Segoe UI", 9)).pack(side="right", padx=(0, 2))

        self._source_var = tk.StringVar(value="Auto Detect")
        source_cb = ttk.Combobox(
            bar, textvariable=self._source_var,
            values=SRC_NAMES, width=12, state="readonly",
            font=("Segoe UI", 9),
        )
        source_cb.pack(side="right", padx=(0, 4), pady=8)
        source_cb.bind("<<ComboboxSelected>>", self._on_source_lang)

    def _build_capture_row(self):
        bar = tk.Frame(self.root, bg=BG2, height=56)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        self._capture_btn = tk.Button(
            bar,
            text="⊞  Capture Region  [Space]",
            command=self._start_capture,
            bg=ACCENT, fg=BG, relief="flat",
            activebackground="#3ab890", activeforeground=BG,
            font=("Segoe UI", 12, "bold"),
            padx=20, pady=6, cursor="hand2",
        )
        self._capture_btn.pack(side="left", padx=14, pady=8)

        self._progress_var = tk.StringVar(value="")
        tk.Label(
            bar, textvariable=self._progress_var,
            bg=BG2, fg=DIM, font=("Segoe UI", 9),
        ).pack(side="left", padx=4)

    def _build_body(self):
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=10, pady=8)

        # --- Top row: preview thumbnail + detected text ---
        top = tk.Frame(body, bg=BG)
        top.pack(fill="x", pady=(0, 4))

        # Preview
        pf = tk.Frame(top, bg=BG2, bd=0)
        pf.pack(side="left", padx=(0, 10))

        tk.Label(pf, text="CAPTURE PREVIEW", bg=BG2, fg=ACCENT,
                 font=("Consolas", 7, "bold")).pack(anchor="w", padx=4, pady=(4, 0))

        self._preview_lbl = tk.Label(
            pf, bg=BG3, width=40, height=14,
            text="Select a region\nto see preview",
            fg=DIM, font=("Segoe UI", 9),
        )
        self._preview_lbl.pack(padx=4, pady=(0, 4))

        # Detected text
        df = tk.Frame(top, bg=BG)
        df.pack(side="left", fill="both", expand=True)

        tk.Label(df, text="DETECTED TEXT", bg=BG, fg=ACCENT,
                 font=("Consolas", 7, "bold")).pack(anchor="w")

        det_scroll = tk.Scrollbar(df, orient="vertical")
        self._detected_txt = tk.Text(
            df, bg=BG2, fg=TEXT, font=("Consolas", 12),
            wrap="word", relief="flat", state="disabled",
            yscrollcommand=det_scroll.set, height=8,
        )
        det_scroll.config(command=self._detected_txt.yview)
        det_scroll.pack(side="right", fill="y")
        self._detected_txt.pack(fill="both", expand=True)

        # --- Reading / phonetics section ---
        tk.Frame(body, bg=BG3, height=1).pack(fill="x", pady=(0, 4))

        rh = tk.Frame(body, bg=BG)
        rh.pack(fill="x")

        self._reading_label_var = tk.StringVar(value="READING")
        tk.Label(rh, textvariable=self._reading_label_var,
                 bg=BG, fg=GOLD, font=("Consolas", 7, "bold")).pack(side="left")

        rf = tk.Frame(body, bg=BG)
        rf.pack(fill="x", pady=(2, 4))

        rs = tk.Scrollbar(rf, orient="vertical")
        self._reading_txt = tk.Text(
            rf, bg=BG2, fg=GOLD,
            font=("Segoe UI", 13), wrap="word",
            relief="flat", state="disabled",
            yscrollcommand=rs.set, height=3,
        )
        rs.config(command=self._reading_txt.yview)
        rs.pack(side="right", fill="y")
        self._reading_txt.pack(fill="both", expand=True)

        # --- Translation area ---
        tk.Frame(body, bg=BG3, height=1).pack(fill="x", pady=(0, 4))

        th = tk.Frame(body, bg=BG)
        th.pack(fill="x")

        tk.Label(th, text="TRANSLATION", bg=BG, fg=ACC2,
                 font=("Consolas", 7, "bold")).pack(side="left")

        tk.Button(
            th, text="Copy",
            command=self._copy_translation,
            bg=BG3, fg=DIM, relief="flat",
            activebackground=BG2, activeforeground=WHITE,
            font=("Segoe UI", 8), padx=6,
        ).pack(side="right")

        ts = tk.Scrollbar(body, orient="vertical")
        self._translation_txt = tk.Text(
            body, bg=BG2, fg=WHITE,
            font=("Segoe UI", 14), wrap="word",
            relief="flat", state="disabled",
            yscrollcommand=ts.set,
        )
        ts.config(command=self._translation_txt.yview)
        ts.pack(side="right", fill="y")
        self._translation_txt.pack(fill="both", expand=True)

    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=BG3, height=22)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self._status_var = tk.StringVar(value="Ready")
        tk.Label(
            bar, textvariable=self._status_var,
            bg=BG3, fg=DIM, font=("Consolas", 7), anchor="w",
        ).pack(side="left", padx=8, pady=4)

        self._char_var = tk.StringVar(value="")
        tk.Label(
            bar, textvariable=self._char_var,
            bg=BG3, fg=DIM, font=("Consolas", 7), anchor="e",
        ).pack(side="right", padx=8, pady=4)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self):
        self._status_var.set(
            "Space: capture  |  Ctrl+Space: show/hide  |  Set Source language for CJK"
        )
        self.root.bind("<space>", lambda _: self._start_capture())
        self.root.mainloop()

    # ------------------------------------------------------------------
    # Capture flow
    # ------------------------------------------------------------------

    def _start_capture(self):
        if self._busy:
            return
        self._busy = True
        self._capture_btn.config(state="disabled")
        self._progress_var.set("Preparing...")
        self.root.iconify()
        self.root.update()
        self.root.after(180, self._do_capture)

    def _do_capture(self):
        from region_selector import RegionSelector
        self._progress_var.set("")

        result = RegionSelector().select(self.root)

        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

        if result is None:
            self._status_var.set("Cancelled.")
            self._set_ready()
            return

        image, x1, y1, x2, y2 = result
        w, h = x2 - x1, y2 - y1
        self._status_var.set(f"OCR running on {w}×{h} px region…")
        self._progress_var.set("Processing…")
        threading.Thread(target=self._run_ocr, args=(image, x1, y1, x2, y2),
                         daemon=True).start()

    def _run_ocr(self, image: Image.Image, x1, y1, x2, y2):
        try:
            text, translation = self._proc.process_region(image)
            reading = self._proc.get_reading(text)
            self.root.after(0, self._update_ui, image, text, reading, translation, x1, y1, x2, y2)
        except Exception as exc:
            self.root.after(0, self._status_var.set, f"Error: {exc}")
        finally:
            self.root.after(0, self._set_ready)

    # ------------------------------------------------------------------
    # UI updates (main thread only)
    # ------------------------------------------------------------------

    def _update_ui(self, image: Image.Image, text: str, reading: str,
                   translation: str, x1, y1, x2, y2):
        # Thumbnail
        thumb = image.copy()
        thumb.thumbnail((300, 210), Image.LANCZOS)
        photo = ImageTk.PhotoImage(thumb)
        self._preview_lbl.config(image=photo, text="")
        self._preview_photo = photo

        self._set_text(self._detected_txt, text or "(no text detected)")

        # Reading section
        self._reading_label_var.set(self._proc.reading_label())
        if reading:
            self._set_text(self._reading_txt, reading)
        else:
            src = self._proc.source_lang
            msg = "— Select Japanese, Chinese, or Korean as Source for phonetic reading"
            if src not in ("auto", "en", "id", "fr", "de", "es", "pt", "vi"):
                msg = "— Phonetic reading not supported for this language yet"
            self._set_text(self._reading_txt, msg)

        self._set_text(self._translation_txt, translation or "—")

        self._status_var.set(
            f"Region: ({x1}, {y1}) → ({x2}, {y2})  |  "
            f"Target: {self._proc.target_lang}"
        )
        self._char_var.set(f"{len(text)} chars")

    def _set_ready(self):
        self._busy = False
        self._progress_var.set("")
        self._capture_btn.config(state="normal")

    @staticmethod
    def _set_text(widget: tk.Text, value: str):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.config(state="disabled")

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def _toggle_pin(self):
        self.root.wm_attributes("-topmost", self._pinned.get())

    def _on_source_lang(self, _event=None):
        name = self._source_var.get()
        self._proc.set_source_lang(SRC_CODE.get(name, "auto"))

    def _on_target_lang(self, _event=None):
        name = self._target_var.get()
        self._proc.set_target_lang(LANG_CODE.get(name, "en"))

    def _copy_translation(self):
        self.root.clipboard_clear()
        try:
            self.root.clipboard_append(
                self._translation_txt.get("1.0", "end").strip()
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Global hotkey (Ctrl+Space) — show / hide
    # ------------------------------------------------------------------

    def _setup_hotkey(self):
        ctypes.windll.user32.RegisterHotKey(None, _HK_ID, _MOD_CTRL, _VK_SPACE)
        threading.Thread(target=self._hotkey_listener, daemon=True).start()

    def _hotkey_listener(self):
        msg = ctypes.wintypes.MSG()
        while not self._quit_flag:
            if ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), None,
                                                  _WM_HOTKEY, _WM_HOTKEY, 1):
                if msg.wParam == _HK_ID:
                    self.root.after(0, self._toggle_visibility)
            time.sleep(0.05)
        ctypes.windll.user32.UnregisterHotKey(None, _HK_ID)

    def _toggle_visibility(self):
        if self.root.state() == "withdrawn":
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        else:
            self.root.withdraw()

    def _quit(self):
        self._quit_flag = True
        self.root.destroy()
