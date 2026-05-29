# Usage Guide

## Prerequisites

### Python 3.10+

Download from [python.org](https://www.python.org/downloads/). During install, check **"Add Python to PATH"**.

### Tesseract OCR

1. Download the installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) (choose the `tesseract-ocr-w64-setup-*.exe` file).
2. Run it — the default install path is `C:\Program Files\Tesseract-OCR\`.
3. Open `screen_processor.py` and set line 15 to your actual install path:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### Tesseract Language Packs

The default Tesseract installer includes English only. For other languages you need the matching `.traineddata` file:

1. Go to the [tessdata repository](https://github.com/tesseract-ocr/tessdata).
2. Download the file for your language (e.g. `jpn.traineddata` for Japanese).
3. Place it in your Tesseract `tessdata` folder, typically:
   `C:\Program Files\Tesseract-OCR\tessdata\`

| Language | File |
|---|---|
| Japanese | `jpn.traineddata` |
| Chinese Simplified | `chi_sim.traineddata` |
| Chinese Traditional | `chi_tra.traineddata` |
| Korean | `kor.traineddata` |
| Indonesian | `ind.traineddata` |
| French | `fra.traineddata` |
| German | `deu.traineddata` |
| Spanish | `spa.traineddata` |
| Arabic | `ara.traineddata` |
| Russian | `rus.traineddata` |
| Hindi | `hin.traineddata` |
| Portuguese | `por.traineddata` |
| Vietnamese | `vie.traineddata` |
| Thai | `tha.traineddata` |

> **CJK tip:** For Japanese, Chinese, and Korean the app uses **EasyOCR** as the primary engine (much more accurate for those scripts). Tesseract is only used as a fallback. EasyOCR downloads its model weights (~100 MB) on the first capture — this can take 5–10 seconds on a fresh install.

## Installing Python Dependencies

Run the setup script from the project folder:

```bat
install.bat
```

It installs everything from `requirements.txt` and checks whether Tesseract is on your PATH.

To install manually:

```bat
pip install -r requirements.txt
```

## Running the App

**With a console window** (useful for seeing error messages):

```bat
python main.py
```

**Without a console window** (clean launch):

Double-click **`TranslatorScreen.vbs`** in File Explorer.

## First Run

On the very first capture with a CJK source language, EasyOCR will print download progress to the console while it fetches the model. This only happens once — subsequent runs load the cached model instantly.

## Step-by-Step: Translating Text

1. **Launch the app.** The panel appears in the centre of your screen.
2. **Set Source language** (top-left dropdown). Use *Auto Detect* for mixed or unknown scripts. For Japanese, Chinese, or Korean, set the source explicitly to get the correct OCR engine and phonetic reading.
3. **Set Target language** (top-right dropdown). Default is Indonesian.
4. **Press `Space`** or click **⊞ Capture Region**. The panel minimises and a dimmed fullscreen overlay appears.
5. **Click and drag** a rectangle around the text. A live preview of the selected area is shown inside the rectangle as you drag.
6. **Release the mouse button** to confirm. The panel reappears with:
   - **Capture Preview** — thumbnail of the selected region.
   - **Detected Text** — raw OCR output.
   - **Reading** — phonetic transcription (Japanese/Chinese/Korean only).
   - **Translation** — the translated result.
7. Click **Copy** to copy the translation to your clipboard.

Press **`ESC`** at any point during the overlay to cancel without translating.

## Language Settings

### Source language

Sets the OCR engine and phonetic reading system:

- **Auto Detect** — Tesseract tries to guess the language. Works for most Latin scripts. Less reliable for CJK.
- **Japanese / Chinese / Korean** — switches the primary OCR engine to EasyOCR for much higher accuracy, and enables the phonetic reading row.

### Target language

The language you want the translation rendered in. Can be changed at any time; the next capture will use the new setting.

### Phonetic readings

| Source | Reading system | Example |
|---|---|---|
| Japanese | Romaji (Hepburn) | `nihongo` |
| Chinese (S/T) | Pinyin (with tones) | `pǔ tōng huà` |
| Korean | Academic Romanization | `hangug-eo` |

For all other source languages the Reading row is hidden.

## Controls Reference

| Control | Action |
|---|---|
| `Space` | Start region capture |
| `Ctrl+Space` (global) | Show or hide the panel from any application |
| `ESC` | Cancel an in-progress capture |
| Opacity slider | Adjust window transparency (0.3 – 1.0) |
| Pin checkbox | Keep the panel on top of all other windows |
| Copy button | Copy translation text to clipboard |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `[Tesseract not installed — run install.bat]` | Tesseract binary not found | Run `install.bat`; check the path in `screen_processor.py` |
| `[Tesseract language pack 'jpn' is not installed]` | Missing `.traineddata` file | Download the file and place it in the Tesseract `tessdata` folder (see above) |
| OCR returns garbage for Japanese/Chinese/Korean | EasyOCR model not downloaded yet | Wait for the first-run download; check internet connection |
| `[Translation error: ...]` | Google Translate API unreachable | Check your internet connection; try again |
| Panel won't appear after `Ctrl+Space` | Hotkey registration failed (another app owns it) | Close conflicting apps; restart Translator Screen |
| Window has no blur / appears solid | Running on Windows 10 older than 1903, or in a VM | Acrylic blur is only available on Windows 10 1903+ and Windows 11; the app still works, just without the blur effect |
| App crashes on first EasyOCR capture | Not enough RAM or disk space | EasyOCR needs ~2 GB RAM and ~500 MB disk for the model cache |
