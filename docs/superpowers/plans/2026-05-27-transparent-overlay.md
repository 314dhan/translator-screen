# Transparent Overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Translator Screen window a frosted-glass semi-transparent overlay using Windows Acrylic via ctypes, with a live opacity slider in the topbar.

**Architecture:** Extract a module-level `apply_acrylic(hwnd, tint_color)` function in `translator_ui.py` that calls `SetWindowCompositionAttribute` via ctypes. `TranslatorUI._build_root()` calls it after the window is realized; `_build_topbar()` adds a `ttk.Scale` slider that adjusts `-alpha` live. A `try/except` around the ctypes call provides a silent fallback on Windows 10/VMs.

**Tech Stack:** Python 3, Tkinter, ctypes (stdlib), `unittest.mock` for tests — no new pip dependencies.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `translator_ui.py` | Modify | Add constants, `apply_acrylic()`, `_on_opacity_change()`, wire into `_build_root()` and `_build_topbar()` |
| `tests/test_transparent_overlay.py` | Create | Unit-test `apply_acrylic` and `_on_opacity_change` without a display |

---

## Task 1: Create tests directory and write failing tests

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_transparent_overlay.py`

- [ ] **Step 1.1 — Create the tests package**

```powershell
New-Item -ItemType Directory -Force tests
New-Item -ItemType File -Path tests\__init__.py
```

- [ ] **Step 1.2 — Write the failing test file**

Create `tests/test_transparent_overlay.py` with this exact content:

```python
# tests/test_transparent_overlay.py
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, ".")


class TestApplyAcrylic(unittest.TestCase):

    def test_passes_hwnd_to_set_window_composition_attribute(self):
        """apply_acrylic forwards the hwnd as the first argument."""
        from translator_ui import apply_acrylic
        with patch("ctypes.windll") as mock_windll:
            apply_acrylic(12345, 0x80000000)
        first_arg = mock_windll.user32.SetWindowCompositionAttribute.call_args[0][0]
        self.assertEqual(first_arg, 12345)

    def test_propagates_exception_on_api_failure(self):
        """apply_acrylic raises if SetWindowCompositionAttribute fails (caller handles fallback)."""
        from translator_ui import apply_acrylic
        with patch("ctypes.windll") as mock_windll:
            mock_windll.user32.SetWindowCompositionAttribute.side_effect = OSError("mock")
            with self.assertRaises(OSError):
                apply_acrylic(99999, 0x80000000)


class TestOpacityChange(unittest.TestCase):

    def _make_ui(self):
        """Create a TranslatorUI instance without calling __init__ or touching Tkinter."""
        from translator_ui import TranslatorUI
        ui = object.__new__(TranslatorUI)
        ui.root = MagicMock()
        return ui

    def test_sets_alpha_from_string_value(self):
        """_on_opacity_change converts the Scale string value to float alpha."""
        ui = self._make_ui()
        ui._on_opacity_change("0.75")
        ui.root.wm_attributes.assert_called_once_with("-alpha", 0.75)

    def test_sets_alpha_at_minimum(self):
        """_on_opacity_change works at the lower bound (0.3)."""
        ui = self._make_ui()
        ui._on_opacity_change("0.3")
        ui.root.wm_attributes.assert_called_once_with("-alpha", 0.3)

    def test_sets_alpha_at_maximum(self):
        """_on_opacity_change works at the upper bound (1.0)."""
        ui = self._make_ui()
        ui._on_opacity_change("1.0")
        ui.root.wm_attributes.assert_called_once_with("-alpha", 1.0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 1.3 — Run tests and confirm they FAIL**

```powershell
cd E:\VDM\translatorscreen
.venv\Scripts\python.exe -m pytest tests/test_transparent_overlay.py -v
```

Expected output: `ImportError` or `AttributeError` — `apply_acrylic` doesn't exist yet and `_on_opacity_change` doesn't exist yet. That's correct — RED phase.

- [ ] **Step 1.4 — Commit the failing tests**

```powershell
rtk git add tests/
rtk git commit -m "test: add failing tests for acrylic overlay and opacity slider"
```

---

## Task 2: Add constants and `apply_acrylic()` to `translator_ui.py`

**Files:**
- Modify: `translator_ui.py` — top of file (after existing color constants, before `LANGS`)

- [ ] **Step 2.1 — Add constants and ctypes structures**

Open `translator_ui.py`. After the line `WHITE  = "#ffffff"` (line 18) and before the blank line before `LANGS`, insert this block:

```python
# ------------------------------------------------------------------
# Transparency / Acrylic
# ------------------------------------------------------------------
import ctypes
import ctypes.wintypes

OPACITY_DEFAULT = 0.88        # initial window alpha
ACRYLIC_TINT    = 0x80000000  # ARGB semi-transparent black tint


class _ACCENTPOLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState",   ctypes.c_uint),
        ("AccentFlags",   ctypes.c_uint),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId",   ctypes.c_uint),
    ]


class _WCAD(ctypes.Structure):  # WINDOWCOMPOSITIONATTRIBDATA
    _fields_ = [
        ("Attribute",  ctypes.c_int),
        ("Data",       ctypes.c_void_p),
        ("SizeOfData", ctypes.c_size_t),
    ]


_ACCENT_ACRYLICBLURBEHIND = 4
_WCA_ACCENT_POLICY        = 19


def apply_acrylic(hwnd: int, tint_color: int) -> None:
    """Apply Windows Acrylic blur behind a window given its HWND.

    Raises OSError / AttributeError on platforms that don't support
    SetWindowCompositionAttribute (Windows 10 or VMs). Caller is
    responsible for catching and falling back.
    """
    accent = _ACCENTPOLICY()
    accent.AccentState   = _ACCENT_ACRYLICBLURBEHIND
    accent.AccentFlags   = 2
    accent.GradientColor = tint_color

    data = _WCAD()
    data.Attribute  = _WCA_ACCENT_POLICY
    data.Data       = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)
    data.SizeOfData = ctypes.sizeof(accent)

    ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
```

- [ ] **Step 2.2 — Run the acrylic tests and confirm they PASS**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_transparent_overlay.py::TestApplyAcrylic -v
```

Expected:
```
PASSED tests/test_transparent_overlay.py::TestApplyAcrylic::test_passes_hwnd_to_set_window_composition_attribute
PASSED tests/test_transparent_overlay.py::TestApplyAcrylic::test_propagates_exception_on_api_failure
```

- [ ] **Step 2.3 — Commit**

```powershell
rtk git add translator_ui.py
rtk git commit -m "feat: add apply_acrylic() and overlay constants to translator_ui"
```

---

## Task 3: Wire `apply_acrylic` into `_build_root()`

**Files:**
- Modify: `translator_ui.py` — `_build_root()` method (currently lines 66–78)

- [ ] **Step 3.1 — Edit `_build_root()` to call `apply_acrylic` after window is realized**

Replace the existing `_build_root` method body with:

```python
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

    # Apply acrylic frosted-glass blur (Windows 11). Falls back silently.
    self.root.update()
    try:
        apply_acrylic(self.root.winfo_id(), ACRYLIC_TINT)
    except Exception:
        pass  # Windows 10 / VM / RDP — plain alpha fallback is fine
    self.root.wm_attributes("-alpha", OPACITY_DEFAULT)
```

- [ ] **Step 3.2 — Smoke-test: launch the app and confirm it opens with transparency**

```powershell
.venv\Scripts\python.exe main.py
```

Expected: window opens, background is visibly frosted/transparent over whatever is behind it. Close it.

- [ ] **Step 3.3 — Commit**

```powershell
rtk git add translator_ui.py
rtk git commit -m "feat: apply acrylic blur and default alpha in _build_root"
```

---

## Task 4: Add opacity slider to `_build_topbar()`

**Files:**
- Modify: `translator_ui.py` — `_build_topbar()` and new `_on_opacity_change()` method

- [ ] **Step 4.1 — Add `_on_opacity_change` method to `TranslatorUI`**

After the `_toggle_pin` method (around line 371), add:

```python
def _on_opacity_change(self, value: str) -> None:
    """Live callback for the opacity slider — updates window alpha."""
    self.root.wm_attributes("-alpha", float(value))
```

- [ ] **Step 4.2 — Run the opacity tests and confirm they PASS**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_transparent_overlay.py::TestOpacityChange -v
```

Expected:
```
PASSED tests/test_transparent_overlay.py::TestOpacityChange::test_sets_alpha_from_string_value
PASSED tests/test_transparent_overlay.py::TestOpacityChange::test_sets_alpha_at_minimum
PASSED tests/test_transparent_overlay.py::TestOpacityChange::test_sets_alpha_at_maximum
```

- [ ] **Step 4.3 — Add slider widget to `_build_topbar()`**

In `_build_topbar()`, **before** the Pin `Checkbutton` block (i.e., insert before the `self._pinned = tk.BooleanVar(...)` line), add:

```python
# Opacity slider
tk.Label(
    bar, text="Opacity:", bg=BG3, fg=DIM,
    font=("Segoe UI", 9),
).pack(side="right", padx=(0, 2))

self._opacity_var = tk.DoubleVar(value=OPACITY_DEFAULT)
ttk.Scale(
    bar,
    from_=0.3, to=1.0,
    variable=self._opacity_var,
    orient="horizontal",
    length=80,
    command=self._on_opacity_change,
).pack(side="right", padx=(0, 6), pady=10)
```

- [ ] **Step 4.4 — Launch the app and verify slider works**

```powershell
.venv\Scripts\python.exe main.py
```

Expected:
- Topbar shows `Opacity:` label + horizontal slider between the language dropdowns and Pin checkbox
- Dragging the slider left makes the window more transparent; right makes it more opaque
- Window is still always-on-top and functional

Close the app.

- [ ] **Step 4.5 — Run all tests one final time**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_transparent_overlay.py -v
```

Expected: **5 tests, all PASSED.**

- [ ] **Step 4.6 — Final commit**

```powershell
rtk git add translator_ui.py
rtk git commit -m "feat: add opacity slider to topbar for live transparency control"
```

---

## Done

All spec requirements are covered:

| Spec requirement | Task |
|-----------------|------|
| Frosted-glass acrylic background | Task 2 + 3 |
| `OPACITY_DEFAULT = 0.88` constant | Task 2 |
| `ACRYLIC_TINT = 0x80000000` constant | Task 2 |
| HWND via `winfo_id()` | Task 3 |
| Fallback to plain `-alpha` on failure | Task 3 |
| Opacity slider in topbar (0.3–1.0) | Task 4 |
| Slider adjusts alpha live | Task 4 |
| Only `translator_ui.py` changed | All tasks |
