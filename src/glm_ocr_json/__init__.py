"""GLM OCR to JSON conversion utilities."""

from .discovery import discover_images
from .ocr import OCRTask, OCRProcessor, OCRResult

__all__ = ["OCRTask", "OCRProcessor", "OCRResult", "discover_images"]
