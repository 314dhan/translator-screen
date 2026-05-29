# Translator Screen

Drag a rectangle over any text on your screen — it gets OCR'd and translated in seconds.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Translator Screen   Source: [Auto Detect ▼]  → Target: [Indonesian ▼] │
│                                        Opacity: [────●──]   [✓ Pin]     │
├─────────────────────────────────────────────────────────────────────────┤
│  ⊞  Capture Region  [Space]                                             │
├────────────────────────┬────────────────────────────────────────────────┤
│  CAPTURE PREVIEW       │  DETECTED TEXT                                 │
│  ┌──────────────────┐  │  ┌──────────────────────────────────────────┐ │
│  │                  │  │  │  翻訳されたテキストがここに表示されます   │ │
│  │  (screen crop)   │  │  │                                          │ │
│  └──────────────────┘  │  └──────────────────────────────────────────┘ │
├────────────────────────┴────────────────────────────────────────────────┤
│  READING  (Romaji — Hepburn)                                            │
│  honyaku sareta tekisuto ga koko ni hyoji sa remasu                     │
├─────────────────────────────────────────────────────────────────────────┤
│  TRANSLATION                                                    [Copy]  │
│                                                                         │
│  Teks yang diterjemahkan akan ditampilkan di sini                       │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  Space: capture  |  Ctrl+Space: show/hide  |  Set Source for CJK       │
└─────────────────────────────────────────────────────────────────────────┘
```

## Features

- **Drag-to-select** — draw a rectangle over any part of your screen to capture text
- **OCR** — EasyOCR for Japanese/Chinese/Korean; Tesseract for all other languages
- **Translation** — powered by Google Translate via `deep-translator`
- **Phonetic readings** — Romaji (Japanese), Pinyin (Chinese), Romanization (Korean)
- **15 languages** — Auto Detect, English, Indonesian, Japanese, Korean, Chinese (Simplified/Traditional), French, German, Spanish, Arabic, Russian, Hindi, Portuguese, Vietnamese, Thai
- **Always-on-top** overlay with Windows Acrylic blur and adjustable opacity
- **Global hotkey** `Ctrl+Space` — show or hide the panel from anywhere
- **No console window** — launch silently via `TranslatorScreen.vbs`

## Requirements

| Requirement | Version |
|---|---|
| Windows | 10 or 11 (64-bit) |
| Python | 3.10 or newer |
| Tesseract OCR | 5.x (must be installed separately) |

> **Note:** This app uses Windows-only APIs (`SetWindowCompositionAttribute`, `RegisterHotKey`) and will not run on macOS or Linux.

## Installation

### 1. Install Tesseract OCR

Download and run the installer from the [UB Mannheim build](https://github.com/UB-Mannheim/tesseract/wiki).
Default install path: `C:\Program Files\Tesseract-OCR\`

For CJK languages (Japanese, Chinese, Korean) you also need the matching language data packs — see [USAGE.md](USAGE.md#tesseract-language-packs) for details.

### 2. Install Python dependencies

```bat
install.bat
```

Or manually:

```bat
pip install -r requirements.txt
```

### 3. Run the app

```bat
python main.py
```

Or double-click **`TranslatorScreen.vbs`** to launch without a console window.

## Building an Executable

To build a standalone `.exe` (no Python required to run):

```bat
build.bat
```

The output is in `dist\TranslatorScreen\`. Share the entire folder — the `.exe` alone won't work without the supporting files next to it.

> The folder will be **1–2 GB** because EasyOCR bundles PyTorch. Tesseract OCR still needs to be installed separately by the end user, but its path is detected automatically.

## Usage

1. Press **`Space`** (or click **Capture Region**) — the panel minimises and a crosshair overlay appears.
2. Click and drag a rectangle around the text you want to translate.
3. Release — the panel comes back with the detected text, phonetic reading (CJK), and translation.
4. Click **Copy** to copy the translation to your clipboard.

## Hotkeys

| Key | Action |
|---|---|
| `Space` | Start region capture |
| `Ctrl+Space` | Show / hide the panel (works globally) |
| `ESC` | Cancel an in-progress capture |

## Supported Languages

| Language | Source | Target | Phonetic reading |
|---|---|---|---|
| Auto Detect | ✓ | — | — |
| English | ✓ | ✓ | — |
| Indonesian | ✓ | ✓ | — |
| Japanese | ✓ | ✓ | Romaji (Hepburn) |
| Korean | ✓ | ✓ | Romanization |
| Chinese (Simplified) | ✓ | ✓ | Pinyin |
| Chinese (Traditional) | ✓ | ✓ | Pinyin |
| French | ✓ | ✓ | — |
| German | ✓ | ✓ | — |
| Spanish | ✓ | ✓ | — |
| Arabic | ✓ | ✓ | — |
| Russian | ✓ | ✓ | — |
| Hindi | ✓ | ✓ | — |
| Portuguese | ✓ | ✓ | — |
| Vietnamese | ✓ | ✓ | — |
| Thai | ✓ | ✓ | — |

## Detailed guide

See [USAGE.md](USAGE.md) for step-by-step instructions, Tesseract language pack setup, and troubleshooting.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
