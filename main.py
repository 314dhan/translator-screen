"""
Translator Screen — entry point.
"""
from screen_processor import ScreenProcessor
from translator_ui import TranslatorUI


def main():
    processor = ScreenProcessor(source_lang="auto", target_lang="id")
    ui = TranslatorUI(processor)
    ui.run()


if __name__ == "__main__":
    main()
