# -*- coding: utf-8 -*-
"""
OCR and translation for an explicitly provided PIL image.
"""
import re
import threading

import cv2
import numpy as np
from PIL import Image

try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Users\rdhan\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
    )
    _TESSERACT_OK = True
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        _TESSERACT_OK = False
except ImportError:
    _TESSERACT_OK = False

# Maps app language code → Tesseract lang code
TESS_LANG = {
    "auto":  "eng",
    "en":    "eng",
    "id":    "ind",
    "ja":    "jpn",
    "ko":    "kor",
    "zh-CN": "chi_sim",
    "zh-TW": "chi_tra",
    "fr":    "fra",
    "de":    "deu",
    "es":    "spa",
    "ar":    "ara",
    "ru":    "rus",
    "hi":    "hin",
    "pt":    "por",
    "vi":    "vie",
    "th":    "tha",
}

# These scripts need lighter image preprocessing (no aggressive threshold)
_CJK_TESS = {"jpn", "chi_sim", "chi_tra", "kor"}

# EasyOCR lang codes for CJK languages (much more accurate than Tesseract)
_EASYOCR_LANG = {
    "ja":    ["ja"],
    "zh-CN": ["ch_sim"],
    "zh-TW": ["ch_tra"],
    "ko":    ["ko"],
}

# Cached EasyOCR readers (initialization is slow — only done once per lang)
_easyocr_readers: dict = {}


def _easy_ocr(image_rgb: np.ndarray, lang_codes: list) -> str | None:
    """Try EasyOCR on an RGB numpy array. Returns None if not installed or fails."""
    try:
        import easyocr
        key = tuple(lang_codes)
        if key not in _easyocr_readers:
            _easyocr_readers[key] = easyocr.Reader(lang_codes, gpu=False, verbose=False)
        reader = _easyocr_readers[key]
        results = reader.readtext(image_rgb, detail=0)
        # CJK text has no word spaces — join without separator
        return "".join(results).strip() or None
    except ImportError:
        return None
    except Exception:
        return None


# ------------------------------------------------------------------
# Romanization helpers (lazy-imported to avoid startup cost)
# ------------------------------------------------------------------

_kakasi = None   # pykakasi instance cache


def _japanese_reading(text: str) -> str:
    global _kakasi
    try:
        import pykakasi
        if _kakasi is None:
            _kakasi = pykakasi.kakasi()
        result = _kakasi.convert(text)
        parts = []
        for item in result:
            hb = item.get("hepburn", "")
            orig = item.get("orig", "")
            if hb:
                parts.append(hb)
            elif orig.strip() == "":
                if parts and not parts[-1].endswith(" "):
                    parts.append(" ")
        return " ".join(parts).strip()
    except ImportError:
        return "[Install pykakasi: pip install pykakasi]"
    except Exception as exc:
        return f"[Reading error: {exc}]"


def _chinese_reading(text: str) -> str:
    try:
        from pypinyin import lazy_pinyin, Style
        result = lazy_pinyin(text, style=Style.TONE)
        return " ".join(result).strip()
    except ImportError:
        return "[Install pypinyin: pip install pypinyin]"
    except Exception as exc:
        return f"[Reading error: {exc}]"


def _korean_reading(text: str) -> str:
    try:
        from hangul_romanize import Transliter
        from hangul_romanize.rule import academic
        tr = Transliter(academic)
        return tr.translit(text)
    except ImportError:
        return "[Install hangul-romanize: pip install hangul-romanize]"
    except Exception as exc:
        return f"[Reading error: {exc}]"


def _available_tess_langs() -> set[str]:
    try:
        import pytesseract as tess
        return set(tess.get_languages())
    except Exception:
        return {"eng"}


_AVAIL_LANGS: set[str] | None = None   # lazy cache


class ScreenProcessor:
    def __init__(self, source_lang: str = "auto", target_lang: str = "en"):
        self.source_lang  = source_lang
        self.target_lang  = target_lang
        self.tesseract_ok = _TESSERACT_OK
        self._translator  = self._make_translator(source_lang, target_lang)
        self._lock        = threading.Lock()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def set_source_lang(self, lang: str):
        self.source_lang = lang
        self._translator = self._make_translator(lang, self.target_lang)

    def set_target_lang(self, lang: str):
        self.target_lang = lang
        self._translator = self._make_translator(self.source_lang, lang)

    def process_region(self, image: Image.Image) -> tuple[str, str]:
        """OCR + translate a PIL image. Returns (detected_text, translation)."""
        text        = self._ocr(image)
        translation = self._translate(text) if text else ""
        return text, translation

    def get_reading(self, text: str) -> str:
        """Return phonetic reading of text based on current source language."""
        if not text:
            return ""
        if self.source_lang == "ja":
            return _japanese_reading(text)
        if self.source_lang in ("zh-CN", "zh-TW"):
            return _chinese_reading(text)
        if self.source_lang == "ko":
            return _korean_reading(text)
        return ""  # not applicable for Latin/other scripts

    def reading_label(self) -> str:
        """Human-readable label for the current source language's phonetic system."""
        return {
            "ja":    "READING  (Romaji — Hepburn)",
            "zh-CN": "READING  (Pinyin)",
            "zh-TW": "READING  (Pinyin)",
            "ko":    "READING  (Romanization)",
        }.get(self.source_lang, "READING")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ocr(self, image: Image.Image) -> str:
        if not self.tesseract_ok:
            return "[Tesseract not installed — run install.bat]"

        global _AVAIL_LANGS
        if _AVAIL_LANGS is None:
            _AVAIL_LANGS = _available_tess_langs()

        tess_lang = TESS_LANG.get(self.source_lang, "eng")

        if tess_lang != "eng" and tess_lang not in _AVAIL_LANGS:
            return (
                f"[Tesseract language pack '{tess_lang}' is not installed.\n"
                f"Download it from github.com/tesseract-ocr/tessdata\n"
                f"and place it in your Tesseract tessdata folder,\n"
                f"or switch Source Language to Auto Detect.]"
            )

        arr = np.array(image)  # RGB

        # --- EasyOCR path (primary for CJK — far more accurate than Tesseract) ---
        easy_langs = _EASYOCR_LANG.get(self.source_lang)
        if easy_langs:
            result = _easy_ocr(arr, easy_langs)
            if result:
                return result
            # EasyOCR not installed or returned nothing — fall through to Tesseract

        # --- Tesseract fallback ---
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

        # Invert dark-background images first
        if np.mean(gray) < 128:
            gray = 255 - gray

        h, w = gray.shape

        if tess_lang in _CJK_TESS:
            short_side = min(h, w)
            scale = max(200 / short_side, 4.0)
            gray = cv2.resize(gray, (int(w * scale), int(h * scale)),
                              interpolation=cv2.INTER_CUBIC)
            pad = 30
            gray = cv2.copyMakeBorder(gray, pad, pad, pad, pad,
                                      cv2.BORDER_CONSTANT, value=255)
            _, processed = cv2.threshold(gray, 0, 255,
                                         cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            if h < 100 or w < 100:
                scale = max(100 / h, 100 / w, 2.0)
                gray = cv2.resize(gray, (int(w * scale), int(h * scale)),
                                  interpolation=cv2.INTER_CUBIC)
            processed = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 15, 4,
            )

        import pytesseract as tess

        oem = 1 if tess_lang in _CJK_TESS else 3

        def _run(psm: int) -> str:
            cfg = f"--psm {psm} --oem {oem} -l {tess_lang}"
            raw = tess.image_to_string(processed, config=cfg)
            cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw)
            cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
            cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
            return cleaned.strip()

        if tess_lang in _CJK_TESS:
            result = _run(7) or _run(6) or _run(8) or _run(10)
        else:
            result = _run(6)
        return result

    def _translate(self, text: str) -> str:
        if not text:
            return ""
        try:
            return self._translator.translate(text[:1500]) or ""
        except Exception as exc:
            return f"[Translation error: {exc}]"

    @staticmethod
    def _make_translator(source: str, target: str):
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source=source, target=target)
