# Transparent Overlay — Design Spec
**Date:** 2026-05-27  
**Status:** Approved

---

## Goal

Convert the Translator Screen Tkinter window from a solid dark panel into a semi-transparent, frosted-glass overlay that floats on top of all other windows — so users can read translated text while still seeing the content beneath.

---

## Scope

- **In scope:** `translator_ui.py` only
- **Out of scope:** `main.py`, `screen_processor.py`, `region_selector.py`, `gaze_tracker.py` — no changes

---

## Approach

**Tkinter + Windows Acrylic Blur via `ctypes`**

After the window is realized, call Windows DWM/User32 APIs to composite a frosted-glass blur layer behind the Tkinter canvas. The window frame is kept (not frameless). Dark panel background colors are lightened slightly so the blur layer shows through.

---

## Components

### 1. `_apply_acrylic(hwnd)` — new private method on `TranslatorUI`

Calls two Windows APIs in sequence:

1. `DwmExtendFrameIntoClientArea` (`dwmapi.dll`) — extends the DWM frame into the client area so Windows manages the background blur
2. `SetWindowCompositionAttribute` (`user32.dll`) — sets `WCA_ACCENT_POLICY` with `ACCENT_ENABLE_ACRYLICBLURBEHIND` (state `4`) and a gradient color of `0x80000000` (semi-transparent black)

Called once from `_build_root()` after `self.root.update()` so the HWND is available. The HWND is obtained via `self.root.winfo_id()`, which returns the native Win32 window handle in Tkinter on Windows.

**Fallback:** Wrapped in `try/except`. On failure (Windows 10, VM, older build), silently falls back to `root.wm_attributes("-alpha", OPACITY_DEFAULT)`.

### 2. Opacity Slider — new widget in `_build_topbar()`

- `ttk.Scale` widget, range `0.3` → `1.0`, default `OPACITY_DEFAULT = 0.88`
- Positioned between the language dropdowns and the Pin checkbox
- `command` callback calls `root.wm_attributes("-alpha", slider_value)` live

### 3. New Constants

```python
OPACITY_DEFAULT  = 0.88          # window alpha at startup
ACRYLIC_TINT     = 0x80000000    # ARGB: semi-transparent black tint
```

---

## Background Color Adjustments

The existing BG colors stay the same hex values. The acrylic effect is applied at the OS compositor level — it shows through any areas not covered by opaque widgets. The dark frames (`BG3 = "#16213e"`) will have a subtle frosted-glass look.

No color constant changes are required.

---

## Error Handling / Fallback

```
try:
    _apply_acrylic(hwnd)        # Windows 11 acrylic
except Exception:
    root.wm_attributes("-alpha", OPACITY_DEFAULT)  # plain alpha fallback
```

This ensures the app runs correctly on Windows 10, VMs, and RDP sessions without crashing.

---

## Testing

- Launch app → window background is visibly frosted/transparent
- Move window over other content → background shows through
- Drag opacity slider → transparency changes live
- OCR + translation pipeline still works normally
- Close and reopen → opacity resets to `OPACITY_DEFAULT` (0.88)
- On a Windows 10 machine (or in fallback path) → app opens with plain alpha, no crash

---

## Files Changed

| File | Change |
|------|--------|
| `translator_ui.py` | Add `_apply_acrylic()`, opacity slider, new constants |

---

## Non-Goals

- No frameless window (title bar kept for easy dragging)
- No rounded corners
- No blur intensity control (fixed tint color)
- No persistence of opacity setting between sessions
