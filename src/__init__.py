"""
Enhanced Document Processor - Core Module

This package provides optimized document processing capabilities with multiple
processing strategies for different use cases.
"""

from .enhanced.enhanced_document_processor import EnhancedDocumentProcessor
from .core.fast_pdf_processor import FastPDFProcessor
from .core.optimized_docling_converter import OptimizedDoclingConverter
from .core.hybrid_document_processor import HybridDocumentProcessor

__version__ = "1.0.0"

__all__ = [
    "EnhancedDocumentProcessor",
    "FastPDFProcessor", 
    "OptimizedDoclingConverter",
    "HybridDocumentProcessor"
]

# Convenience imports for common use cases
def create_fast_processor(backend="pymupdf"):
    """Create a fast PDF processor for text extraction."""
    return FastPDFProcessor(backend)

def create_optimized_docling(mode="fast"):
    """Create an optimized Docling processor."""
    return OptimizedDoclingConverter(mode)

def create_hybrid_processor():
    """Create a hybrid processor with intelligent mode selection."""
    return HybridDocumentProcessor()

# Recommended processors by use case
RECOMMENDED_PROCESSORS = {
    "text_search": lambda: create_fast_processor("pymupdf"),
    "table_extraction": lambda: create_fast_processor("pdfplumber"), 
    "structured_analysis": lambda: create_optimized_docling("fast"),
    "full_document": lambda: create_optimized_docling("balanced"),
    "production": lambda: create_hybrid_processor()
}
