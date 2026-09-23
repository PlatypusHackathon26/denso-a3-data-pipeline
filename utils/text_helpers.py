"""Compatibility entry point for shared text helpers."""

from .text_cleaner import clean_blocks, clean_text, collapse_whitespace, dehyphenate

__all__ = ["clean_blocks", "clean_text", "collapse_whitespace", "dehyphenate"]
