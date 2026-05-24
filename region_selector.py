# -*- coding: utf-8 -*-
"""
Fullscreen screenshot overlay for drag-to-select region capture.
"""
import tkinter as tk
from PIL import Image, ImageTk
import mss

ACCENT = "#4ecca3"


class RegionSelector:
    """Show a fullscreen selection overlay on the main thread via wait_window."""

    def select(self, root) -> tuple | None:
        """
        Captures the current screen, shows a dimmed overlay, lets the user
        drag a rectangle, then returns (PIL.Image crop, x1, y1, x2, y2)
        or None if cancelled.
        """
        # --- Grab screen before showing anything ---
        with mss.mss() as sct:
            mon = sct.monitors[0]
            shot = sct.grab(mon)
            orig = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

        sw, sh = orig.size
        dimmed = Image.blend(orig, Image.new("RGB", orig.size, (0, 0, 0)), 0.45)

        result = [None]
        start = [0, 0]
        _rect_id    = [None]
        _size_id    = [None]
        _crop_item  = [None]
        _crop_photo = [None]   # keep reference to prevent GC

        win = tk.Toplevel(root)
        win.overrideredirect(True)
        win.geometry(f"{sw}x{sh}+0+0")
        win.attributes("-topmost", True)
        win.config(cursor="crosshair")
        win.focus_force()

        canvas = tk.Canvas(win, width=sw, height=sh, highlightthickness=0, cursor="crosshair")
        canvas.pack()

        bg_photo = ImageTk.PhotoImage(dimmed)
        canvas.create_image(0, 0, anchor="nw", image=bg_photo)

        # Instruction overlay
        canvas.create_text(
            sw // 2, sh // 2,
            text="Click and drag to select a region to translate",
            fill="white", font=("Segoe UI", 18, "bold"),
            tags="hint",
        )
        canvas.create_text(
            sw // 2, sh // 2 + 36,
            text="Release to confirm  ·  ESC to cancel",
            fill="#aaaaaa", font=("Segoe UI", 12),
            tags="hint",
        )

        def _clear():
            for ref in (_rect_id, _size_id, _crop_item):
                if ref[0]:
                    canvas.delete(ref[0])
                    ref[0] = None

        def on_press(e):
            start[0], start[1] = e.x, e.y
            canvas.delete("hint")
            _clear()

        def on_drag(e):
            _clear()
            x1 = min(start[0], e.x)
            y1 = min(start[1], e.y)
            x2 = max(start[0], e.x)
            y2 = max(start[1], e.y)
            w, h = x2 - x1, y2 - y1

            if w > 2 and h > 2:
                crop = orig.crop((x1, y1, x2, y2))
                photo = ImageTk.PhotoImage(crop)
                _crop_photo[0] = photo
                _crop_item[0] = canvas.create_image(x1, y1, anchor="nw", image=photo)

            _rect_id[0] = canvas.create_rectangle(
                x1, y1, x2, y2, outline=ACCENT, width=2,
            )
            ly = y1 - 22 if y1 > 30 else y2 + 5
            _size_id[0] = canvas.create_text(
                x1, ly,
                text=f" {w} × {h} px ",
                fill=ACCENT, font=("Consolas", 11, "bold"),
                anchor="nw",
            )

        def on_release(e):
            x1 = min(start[0], e.x)
            y1 = min(start[1], e.y)
            x2 = max(start[0], e.x)
            y2 = max(start[1], e.y)
            if x2 - x1 > 10 and y2 - y1 > 10:
                crop = orig.crop((x1, y1, x2, y2))
                result[0] = (crop, x1, y1, x2, y2)
            win.destroy()

        def on_escape(e):
            win.destroy()

        canvas.bind("<ButtonPress-1>",   on_press)
        canvas.bind("<B1-Motion>",       on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        win.bind("<Escape>", on_escape)

        root.wait_window(win)
        return result[0]
