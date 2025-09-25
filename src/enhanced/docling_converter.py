"""
Docling Converter for enhanced document processing.

This module handles the Docling-specific conversion logic, adapted from the
existing MERI codebase for use in the enhanced document processor.
"""

from typing import Optional, Dict, Any
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


class DoclingConverter:
    """Handles document conversion using Docling with enhanced metadata preservation."""

    def __init__(self,
                 preserve_images: bool = True,
                 preserve_tables: bool = True,
                 enable_ocr: bool = False,
                 table_mode: str = "accurate"):
        """
        Initialize the Docling converter.

        Args:
            preserve_images: Whether to extract images from documents
            preserve_tables: Whether to preserve table structures
            enable_ocr: Whether to enable OCR for scanned content
            table_mode: Table extraction mode ('accurate' or 'fast')
        """
        self.preserve_images = preserve_images
        self.preserve_tables = preserve_tables
        self.enable_ocr = enable_ocr
        self.table_mode = table_mode

        # Configure table structure options
        table_mode_map = {
            'accurate': TableFormerMode.ACCURATE,
            'fast': TableFormerMode.FAST
        }

        self.table_structure_options = TableStructureOptions(
            mode=table_mode_map.get(table_mode, TableFormerMode.ACCURATE),
            do_cell_matching=preserve_tables
        )

        # Configure pipeline options
        self.pipeline_options = PdfPipelineOptions(
            generate_picture_images=preserve_images,
            generate_table_images=preserve_tables,
            do_ocr=enable_ocr,
            table_structure_options=self.table_structure_options
        )

        # Initialize the document converter
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=self.pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )

    def convert_document(self,
                        file_path: str,
                        **kwargs) -> Any:
        """
        Convert a document using Docling.

        Args:
            file_path: Path to the document file
            **kwargs: Additional options for conversion

        Returns:
            Docling conversion result with full document structure
        """
        try:
            # Convert the document
            conversion_result = self.converter.convert(file_path)

            # Validate the conversion
            if not conversion_result or not conversion_result.document:
                raise ValueError(f"Failed to convert document: {file_path}")

            return conversion_result

        except Exception as e:
            raise RuntimeError(f"Docling conversion failed for {file_path}: {e}") from e

    def get_document_info(self, conversion_result) -> Dict[str, Any]:
        """
        Extract document information from conversion result.

        Args:
            conversion_result: Docling conversion result

        Returns:
            Dictionary with document metadata
        """
        document = conversion_result.document

        # Count different element types
        element_counts = {
            'pages': len(document.pages),
            'text_items': 0,
            'tables': 0,
            'images': 0,
            'lists': 0,
            'sections': 0
        }

        for item, _ in document.iterate_items():
            if hasattr(item, 'label'):
                label_str = str(item.label).lower()
                if 'text' in label_str or 'paragraph' in label_str:
                    element_counts['text_items'] += 1
                elif 'table' in label_str:
                    element_counts['tables'] += 1
                elif 'picture' in label_str or 'image' in label_str:
                    element_counts['images'] += 1
                elif 'list' in label_str:
                    element_counts['lists'] += 1
                elif 'section' in label_str or 'header' in label_str:
                    element_counts['sections'] += 1

        return {
            'element_counts': element_counts,
            'has_text': element_counts['text_items'] > 0,
            'has_tables': element_counts['tables'] > 0,
            'has_images': element_counts['images'] > 0,
            'has_lists': element_counts['lists'] > 0,
            'has_sections': element_counts['sections'] > 0,
        }

    def extract_text_only(self, conversion_result) -> str:
        """
        Extract only the text content from a conversion result.

        Args:
            conversion_result: Docling conversion result

        Returns:
            Plain text content
        """
        document = conversion_result.document
        text_parts = []

        for item, _ in document.iterate_items():
            if hasattr(item, 'text') and item.text:
                text_parts.append(item.text)

        return '\n'.join(text_parts)

    def extract_structured_content(self, conversion_result) -> Dict[str, Any]:
        """
        Extract structured content with element types and positions.

        Args:
            conversion_result: Docling conversion result

        Returns:
            Structured content dictionary
        """
        document = conversion_result.document
        structured_content = {
            'pages': [],
            'elements': []
        }

        # Process each page
        for page_idx, page in enumerate(document.pages):
            page_info = {
                'page_index': page_idx,
                'size': page.size,
                'elements': []
            }

            # Get elements for this page
            for item, level in document.iterate_items():
                if hasattr(item, 'prov') and item.prov:
                    # Check if this item belongs to current page
                    for prov in item.prov:
                        if prov.page_no - 1 == page_idx:  # page_no is 1-indexed
                            element_info = {
                                'type': str(item.label) if hasattr(item, 'label') else 'unknown',
                                'level': level,
                                'bbox': list(prov.bbox.as_tuple()) if hasattr(prov, 'bbox') else None,
                                'page_index': prov.page_no - 1,
                                'text': item.text if hasattr(item, 'text') else None,
                                'metadata': {}
                            }

                            # Add type-specific metadata
                            if hasattr(item, 'image') and item.image:
                                element_info['metadata']['image_uri'] = item.image.uri
                            elif hasattr(item, 'data') and hasattr(item.data, 'table_cells'):
                                element_info['metadata']['table_cells'] = len(item.data.table_cells)

                            page_info['elements'].append(element_info)
                            break

            structured_content['pages'].append(page_info)
            structured_content['elements'].extend(page_info['elements'])

        return structured_content
