import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from screen_processor import _find_tesseract


def test_find_tesseract_returns_string_or_none():
    result = _find_tesseract()
    assert result is None or isinstance(result, str)


def test_find_tesseract_path_exists_when_found():
    result = _find_tesseract()
    if result is not None:
        assert os.path.isfile(result), f"Returned path does not exist: {result}"


def test_find_tesseract_ends_with_exe_when_found():
    result = _find_tesseract()
    if result is not None:
        assert result.lower().endswith("tesseract.exe")
