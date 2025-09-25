"""
Optimized Docling Converter for faster document processing.

This module provides optimized configurations for Docling to reduce processing time
while maintaining good quality output. Different modes available based on use case.
"""

import time
from typing import Optional, Dict, Any, Literal, List, Tuple
from pathlib import Path

from docling.datamodel.settings import settings

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions, TableFormerMode
    from docling.datamodel.base_models import InputFormat
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    from docling.datamodel.document import DoclingDocument, TextItem, TableItem, PictureItem, ListItem
    from docling_core.types.doc import DocItemLabel
except ImportError as e:
    raise ImportError(
        "Docling dependencies not found. Please install required packages:\n"
        "pip install docling docling-core python-multipart pypdfium2"
    ) from e


class OptimizedDoclingConverter:
    """Optimized Docling converter with different speed/quality modes and enhanced metadata extraction."""

    def __init__(self, mode: Literal["fastest", "fast", "balanced", "quality"] = "fast"):
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
        self._last_processing_time: float = 0.0 # ConversionResult is a Pydantic model and doesn’t allow adding new attributes like processing_time. The documented fields are document, status, errors, and timings, etc.—no processing_time.

    def _create_converter(self) -> DocumentConverter:
        """Create optimized converter based on mode."""
        
        if self.mode == "fastest":
            # Minimal processing - but keep basic structure extraction
            pipeline_options = PdfPipelineOptions(
                generate_picture_images=False,
                generate_table_images=False,
                do_ocr=False,
                table_structure_options=TableStructureOptions(
                    mode=TableFormerMode.FAST,
                    do_cell_matching=False
                )
            )
            # Keep basic table structure for element detection
            pipeline_options.do_table_structure = True
        
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
            pipeline_options.do_table_structure = True
        
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
            pipeline_options.do_table_structure = True
        
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
            pipeline_options.do_table_structure = True

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
        start_time = time.time()
        result = self.converter.convert(file_path)
        # result.processing_time = time.time() - start_time
        self._last_processing_time = time.time() - start_time
        return result

    def extract_document_metadata(self, document: DoclingDocument) -> Dict[str, Any]:
        """Extract comprehensive document structure metadata (using body + provenance)."""
        page_count = getattr(document, "num_pages", None) or len(getattr(document, "pages", []))
        metadata: Dict[str, Any] = {
            "page_count": page_count,
            "processing_mode": self.mode,
            "elements_by_type": {},
            "tables": [],
            "images": [],
            "text_blocks": [],
            "headings": [],
            "bounding_boxes": {},
            "document_structure": [],
        }

        # Pre-create per-page buckets from PageItem 
        page_index = {}
        for page_idx, p in enumerate(getattr(document, "pages", [])):
            # Handle different page object types
            if hasattr(p, "page_no"):
                pn = p.page_no
                page_size = getattr(p, "size", None)
            elif isinstance(p, dict):
                pn = p.get("page_no", page_idx + 1)  # Default to 1-indexed if missing
                page_size = p.get("size")
            else:
                # If p is just an int or other simple type, use index
                pn = page_idx + 1  # 1-indexed page numbers
                page_size = None
                
            page_index[pn] = {
                "page_number": pn,
                "elements": [],
                "tables": [],
                "images": [],
                "text_blocks": [],
                "page_size": page_size,
            }

        def classify(item, lbl) -> str:
            # Use proper isinstance checks as per Docling documentation
            if isinstance(item, TableItem):
                return "table"
            elif isinstance(item, PictureItem):
                return "picture"
            elif isinstance(item, TextItem):
                # Check label for specific text type classification
                if lbl == DocItemLabel.TITLE:
                    return "heading"
                elif lbl == DocItemLabel.SECTION_HEADER:
                    return "heading"
                elif lbl in {DocItemLabel.PARAGRAPH, DocItemLabel.TEXT}:
                    return "text"
                else:
                    return "text"  # Default for other text items
            elif isinstance(item, ListItem):
                return "text"  # Treat list items as text blocks
            else:
                # Handle other document item types by their class name
                item_type = type(item).__name__
                if isinstance(item, int):
                    return "unknown_int"
                elif "Header" in item_type or "Title" in item_type:
                    return "heading"
                elif "Text" in item_type or "Paragraph" in item_type:
                    return "text"
                elif "Table" in item_type:
                    return "table"
                elif "Picture" in item_type or "Image" in item_type:
                    return "picture"
                else:
                    # For any other types, classify as text by default
                    return "text"

        # Walk the body in reading order and group by provenance.page_no
        item_count = 0
        for item, level in document.iterate_items():
            item_count += 1
            
            # Skip if item is just an integer (degraded mode)
            if isinstance(item, int):
                continue
                
            label = getattr(item, "label", None)
            etype = classify(item, label)
            ed: Dict[str, Any] = {
                "type": etype,
                "label": getattr(label, "value", str(label)),
                "text": getattr(item, "text", ""),
            }
            prov_list = getattr(item, "prov", []) or []
            prov = prov_list[0] if prov_list else None
            page_no, bbox = None, None
            if isinstance(prov, int):
                page_no = prov
            elif isinstance(prov, dict):
                page_no = prov.get("page_no"); bbox = prov.get("bbox")
            else:
                page_no = getattr(prov, "page_no", None)
                bbox = getattr(prov, "bbox", None)
            ed["page"] = page_no
            if bbox is not None:
                ed["bbox"] = (bbox.model_dump() if hasattr(bbox, "model_dump") else bbox)
                # Add to main bounding_boxes collection
                bbox_id = f"{etype}_{page_no}_{len(metadata['bounding_boxes'])}"
                metadata["bounding_boxes"][bbox_id] = ed["bbox"]

            # Table specifics
            if etype == "table" and hasattr(item, "data") and item.data is not None:
                td = item.data
                ed["table_metadata"] = {
                    "rows": getattr(td, "num_rows", 0),
                    "columns": getattr(td, "num_cols", 0),
                }
                if getattr(td, "table_cells", None):
                    try:
                        ed["table_content"] = [[getattr(c, "text", "") for c in row] for row in td.table_cells]
                    except Exception:
                        # Fallback if table_cells structure is different
                        ed["table_content"] = []

            # Picture specifics
            if etype == "picture":
                ed["image_metadata"] = {"has_image_ref": getattr(item, "image", None) is not None}

            # Global tallies
            metadata["elements_by_type"][etype] = metadata["elements_by_type"].get(etype, 0) + 1
            if etype == "table":
                metadata["tables"].append(ed)
            elif etype == "picture":
                metadata["images"].append(ed)
            elif etype == "heading":
                metadata["headings"].append(ed)
            elif etype == "text":
                metadata["text_blocks"].append(ed)

            # Per-page aggregation
            pn = ed.get("page", None)
            if pn in page_index:
                page_index[pn]["elements"].append(ed)
                if etype == "table":
                    page_index[pn]["tables"].append(ed)
                elif etype == "picture":
                    page_index[pn]["images"].append(ed)
                elif etype == "text":
                    page_index[pn]["text_blocks"].append(ed)

        metadata["document_structure"] = [page_index[k] for k in sorted(page_index.keys()) if k is not None]
        metadata["summary"] = {
            "total_elements": sum(metadata["elements_by_type"].values()),
            "table_count": len(metadata["tables"]),
            "image_count": len(metadata["images"]),
            "heading_count": len(metadata["headings"]),
            "text_block_count": len(metadata["text_blocks"]),
            "raw_item_count": item_count,  # Total items from iterate_items()
        }
        
        # If we got mostly integers (degraded mode), estimate content from text
        if metadata["summary"]["total_elements"] < 10 and item_count > 100:
            # Fallback: try to extract basic stats from markdown export
            try:
                md_content = document.export_to_markdown()
                lines = md_content.split('\n')
                metadata["summary"]["estimated_text_blocks"] = len([l for l in lines if l.strip() and not l.startswith('#')])
                metadata["summary"]["estimated_headings"] = len([l for l in lines if l.startswith('#')])
                metadata["summary"]["estimated_tables"] = md_content.count('|')  # Simple table detection
                metadata["summary"]["mode_note"] = f"Degraded mode detected - {item_count} raw items, using markdown fallback"
            except Exception:
                metadata["summary"]["mode_note"] = f"Degraded mode detected - {item_count} raw items, no usable structure"
        return metadata

    def _extract_element_metadata(self, element) -> Dict[str, Any]:
        """Extract metadata from a document element."""
        element_data = {
            "type": getattr(element, "label", "unknown"),
            "text": getattr(element, "text", ""),
        }
        
        # Extract bounding box if available
        if hasattr(element, "bbox"):
            bbox = element.bbox
            element_data["bbox"] = {
                "x0": bbox.l if hasattr(bbox, 'l') else getattr(bbox, 'x0', None),
                "y0": bbox.t if hasattr(bbox, 't') else getattr(bbox, 'y0', None),
                "x1": bbox.r if hasattr(bbox, 'r') else getattr(bbox, 'x1', None),
                "y1": bbox.b if hasattr(bbox, 'b') else getattr(bbox, 'y1', None),
                "width": getattr(bbox, 'width', None),
                "height": getattr(bbox, 'height', None)
            }
        
        # Extract table-specific metadata
        if hasattr(element, "table_data") or element_data["type"] == "table":
            table_data = getattr(element, "table_data", None)
            if table_data:
                element_data["table_metadata"] = {
                    "rows": len(table_data.table_cells) if hasattr(table_data, 'table_cells') else 0,
                    "columns": len(table_data.table_cells[0]) if hasattr(table_data, 'table_cells') and table_data.table_cells else 0,
                    "has_header": getattr(table_data, 'has_header', False)
                }
                
                # Extract table content
                if hasattr(table_data, 'table_cells'):
                    element_data["table_content"] = [
                        [cell.text if hasattr(cell, 'text') else str(cell) for cell in row]
                        for row in table_data.table_cells
                    ]
        
        # Extract image metadata
        if hasattr(element, "image") or element_data["type"] == "picture":
            if hasattr(element, "image"):
                image = element.image
                element_data["image_metadata"] = {
                    "format": getattr(image, "format", None),
                    "size": getattr(image, "size", None),
                    "mode": getattr(image, "mode", None)
                }
        
        # Extract font information if available
        if hasattr(element, "font"):
            element_data["font"] = {
                "family": getattr(element.font, "family", None),
                "size": getattr(element.font, "size", None),
                "weight": getattr(element.font, "weight", None),
                "style": getattr(element.font, "style", None)
            }
        
        return element_data

    def get_processing_info(self) -> Dict[str, Any]:
        """Get information about current processing configuration."""
        return {
            "mode": self.mode,
            "features_enabled": {
                "table_extraction": self.mode in ["fast", "balanced", "quality"],
                "image_extraction": self.mode in ["balanced", "quality"],
                "ocr": self.mode == "quality",
                "cell_matching": self.mode in ["fast", "balanced", "quality"]
            },
            "expected_speed": {
                "fastest": "3-5x faster than balanced",
                "fast": "2-3x faster than balanced", 
                "balanced": "baseline speed",
                "quality": "2-3x slower than balanced"
            }[self.mode]
        }

    def create_enhanced_rag_document(self, file_path: str, document_id: Optional[str] = None):
        """Create RAGDocument with enhanced metadata including document structure."""
        try:
            from llama_stack_client import RAGDocument
        except ImportError:
            class RAGDocument:
                def __init__(self, document_id: str, content: Any, mime_type: str, metadata: Optional[Dict] = None):
                    self.document_id = document_id
                    self.content = content
                    self.mime_type = mime_type
                    self.metadata = metadata or {}

        conversion_result = self.convert_document(file_path)
        
        if not conversion_result:
            return None
        
        document_id = document_id or Path(file_path).stem
        
        # Extract content
        content = conversion_result.document.export_to_markdown()
        
        # Extract comprehensive metadata
        document_metadata = self.extract_document_metadata(conversion_result.document)
        
        # Combine with file metadata
        metadata = {
            "file_path": str(file_path),
            "file_type": Path(file_path).suffix.lower(),
            "file_size": Path(file_path).stat().st_size,
            "processing_method": f"docling_{self.mode}",
            # "processing_time": getattr(conversion_result, 'processing_time', 0),
            "processing_time": self._last_processing_time,
            "content_length": len(content),
            **document_metadata,
            "docling_mode_info": self.get_processing_info()
        }
        
        return RAGDocument(
            document_id=document_id,
            content=content,
            mime_type="text/plain",
            metadata=metadata
        )

    def benchmark_processing(self, file_path: str) -> Dict[str, Any]:
        """Benchmark this processor and return detailed performance metrics."""
        start_time = time.time()
        from docling.datamodel.settings import settings
        settings.debug.profile_pipeline_timings = True
        
        try:
            conversion_result = self.convert_document(file_path)
            processing_time = time.time() - start_time
            
            if not conversion_result:
                return {"error": "Conversion failed"}
            
            content = conversion_result.document.export_to_markdown()
            document_metadata = self.extract_document_metadata(conversion_result.document)
            
            return {
                "success": True,
                # "processing_time": processing_time,
                "processing_time": self._last_processing_time,
                "mode": self.mode,
                "content_length": len(content),
                "page_count": len(conversion_result.document.pages),
                "elements_extracted": document_metadata["summary"],
                "file_size": Path(file_path).stat().st_size,
                "processing_speed": f"{len(conversion_result.document.pages) / processing_time:.1f} pages/second",
                "docling_pipeline_secs": (
                    conversion_result.timings.get("pipeline_total").times
                    if hasattr(conversion_result, "timings") and "pipeline_total" in conversion_result.timings
                    else None
                )
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                # "processing_time": time.time() - start_time,
                "processing_time": self._last_processing_time,
                "mode": self.mode
            }


if __name__ == "__main__":
    # Demo the optimized converter
    pdf_path = "data/wartsila46f-project-guide.pdf"
    
    print(f"Looking for test file: {pdf_path}")
    print(f"File exists: {Path(pdf_path).exists()}")
    
    if Path(pdf_path).exists():
        print("Optimized Docling Converter Demo")
        print("=" * 40)
        
        # Test different modes
        for mode in ["fastest", "fast", "balanced"]:
            print(f"\nTesting {mode} mode:")
            print("-" * 20)
            
            try:
                converter = OptimizedDoclingConverter(mode)
                print(f"Created converter for mode: {mode}")
                benchmark = converter.benchmark_processing(pdf_path)
                print(f"Benchmark result: {benchmark}")
                
                if benchmark.get("success"):
                    print(f"Time: {benchmark['processing_time']:.2f}s")
                    print(f"Total pages: {benchmark['page_count']}")
                    print(f"Speed: {benchmark['processing_speed']}")
                    print(f"Elements: {benchmark['elements_extracted']}")
                else:
                    print(f"Error: {benchmark.get('error')}")
            except Exception as e:
                print(f"Exception in {mode} mode: {e}")
                import traceback
                traceback.print_exc()
    else:
        print(f"Test file not found: {pdf_path}")
        print("Place a PDF in the data/ directory to test.")