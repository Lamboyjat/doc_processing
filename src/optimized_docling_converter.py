"""
Optimized Docling Converter for faster document processing.

This module provides optimized configurations for Docling to reduce processing time
while maintaining good quality output. Different modes available based on use case.
"""

from typing import Optional, Dict, Any, Literal
from pathlib import Path

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions, TableFormerMode
    from docling.datamodel.base_models import InputFormat
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
except ImportError as e:
    raise ImportError(
        "Docling dependencies not found. Please install required packages:\n"
        "pip install docling docling-core python-multipart pypdfium2"
    ) from e


class OptimizedDoclingConverter:
    """Optimized Docling converter with different speed/quality modes."""

    def __init__(self, 
                 mode: Literal["fastest", "fast", "balanced", "quality"] = "fast"):
        """
        Initialize with optimization mode.
        
        Args:
            mode: Processing mode
                - "fastest": Text only, no images/tables, no OCR (~3-5x faster)
                - "fast": Basic tables, no images, no OCR (~2-3x faster)
                - "balanced": Tables + images, no OCR (default speed)
                - "quality": Full processing with OCR (slowest, highest quality)
        """
        self.mode = mode
        self.converter = self._create_converter()

    def _create_converter(self) -> DocumentConverter:
        """Create optimized converter based on mode."""
        
        if self.mode == "fastest":
            # Minimal processing - text extraction only
            pipeline_options = PdfPipelineOptions(
                generate_picture_images=False,
                generate_table_images=False,
                do_ocr=False,
                table_structure_options=TableStructureOptions(
                    mode=TableFormerMode.FAST,
                    do_cell_matching=False
                )
            )
        
        elif self.mode == "fast":
            # Fast table extraction, no images
            pipeline_options = PdfPipelineOptions(
                generate_picture_images=False,
                generate_table_images=False,
                do_ocr=False,
                table_structure_options=TableStructureOptions(
                    mode=TableFormerMode.FAST,
                    do_cell_matching=True
                )
            )
        
        elif self.mode == "balanced":
            # Balanced processing
            pipeline_options = PdfPipelineOptions(
                generate_picture_images=True,
                generate_table_images=True,
                do_ocr=False,
                table_structure_options=TableStructureOptions(
                    mode=TableFormerMode.FAST,
                    do_cell_matching=True
                )
            )
        
        else:  # quality
            # Full processing
            pipeline_options = PdfPipelineOptions(
                generate_picture_images=True,
                generate_table_images=True,
                do_ocr=True,
                table_structure_options=TableStructureOptions(
                    mode=TableFormerMode.ACCURATE,
                    do_cell_matching=True
                )
            )

        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )

    def convert_document(self, file_path: str, **kwargs) -> Any:
        """Convert document with optimized settings."""
        return self.converter.convert(file_path)

    def get_processing_info(self) -> Dict[str, Any]:
        """Get information about current processing mode."""
        mode_info = {
            "fastest": {
                "description": "Text extraction only",
                "features": ["Text content"],
                "speed": "3-5x faster",
                "use_case": "Basic text extraction, search indexing"
            },
            "fast": {
                "description": "Fast table extraction, no images",
                "features": ["Text content", "Basic tables"],
                "speed": "2-3x faster", 
                "use_case": "Document analysis with tables"
            },
            "balanced": {
                "description": "Tables and images, no OCR",
                "features": ["Text content", "Tables", "Images"],
                "speed": "Standard speed",
                "use_case": "Full document processing, no scanned content"
            },
            "quality": {
                "description": "Full processing with OCR",
                "features": ["Text content", "Tables", "Images", "OCR"],
                "speed": "Slowest",
                "use_case": "Scanned documents, highest quality needed"
            }
        }
        return mode_info[self.mode]
