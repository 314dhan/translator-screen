# Contributing

## Dev Environment Setup

```bat
git clone https://github.com/314dhan/translator-screen.git
cd translator-screen
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Install Tesseract and update the path in `screen_processor.py` as described in [USAGE.md](USAGE.md#tesseract-ocr).

Run the app:

```bat
python main.py
```

## Project Structure

| File | Purpose |
|---|---|
| `main.py` | Entry point — wires `ScreenProcessor` and `TranslatorUI` together |
| `translator_ui.py` | Main panel UI (tkinter), opacity/pin/hotkey controls |
| `region_selector.py` | Fullscreen drag-to-select overlay (mss screenshot + tkinter canvas) |
| `screen_processor.py` | OCR (EasyOCR + Tesseract) and translation (Google Translate) |
| `gaze_tracker.py` | Webcam eye-tracking via MediaPipe iris landmarks (mouse fallback) |
| `TranslatorScreen.vbs` | Silent launcher — runs `pythonw.exe` so no console appears |
| `install.bat` | One-shot setup: installs pip deps, checks Tesseract |
| `requirements.txt` | Python dependencies |

## Capture Flow

```
Space / button click
  → TranslatorUI._start_capture()
      minimises panel
  → RegionSelector.select()
      fullscreen overlay, drag to pick region
      returns (PIL.Image, x1, y1, x2, y2) or None
  → TranslatorUI._run_ocr()  [background thread]
      ScreenProcessor.process_region(image)
        → _ocr()    EasyOCR (CJK) or Tesseract
        → _translate()  GoogleTranslator
      → get_reading()  pykakasi / pypinyin / hangul-romanize
  → TranslatorUI._update_ui()  [main thread via root.after]
```

## Commit Style

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add clipboard history
fix: correct pinyin tone marks for retroflex consonants
docs: update Tesseract install path instructions
refactor: extract OCR preprocessing into its own function
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

## Pull Requests

1. Fork the repo and create a branch: `git checkout -b feat/my-feature`
2. Make your changes and commit with a clear message.
3. Open a PR against `main` with a short description of what changed and why.

## Areas for Contribution

- **Auto-update Tesseract path** — detect the Tesseract binary from the system PATH or registry instead of requiring a hardcoded path in `screen_processor.py`
- **Additional phonetic systems** — Arabic transliteration, Hindi Devanagari romanization
- **Continuous capture mode** — auto-retranslate on a timer instead of requiring a manual capture
- **History panel** — store previous captures with timestamps
- **Cross-platform port** — abstract the Win32-specific code (`RegisterHotKey`, `SetWindowCompositionAttribute`) behind a platform interface
