"""
Enhanced Document Processor - Main Entry Point

This is your main interface for document processing. Choose the processor
that best fits your needs.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src import (
    FastPDFProcessor,
    OptimizedDoclingConverter, 
    HybridDocumentProcessor,
    RECOMMENDED_PROCESSORS
)

class DocumentProcessor:
    """
    Main document processor interface - your primary entry point.
    
    This class provides a simple interface to all available processing methods
    with automatic optimization recommendations.
    """
    
    def __init__(self, mode="auto"):
        """
        Initialize document processor.
        
        Args:
            mode: Processing mode
                - "auto": Intelligent selection (recommended)
                - "fastest": Ultra-fast text extraction
                - "fast": Fast with tables
                - "balanced": Full features, optimized speed
                - "production": Hybrid with fallbacks
        """
        self.mode = mode
        self.processor = self._create_processor()
    
    def _create_processor(self):
        """Create appropriate processor based on mode."""
        if self.mode == "auto" or self.mode == "production":
            return HybridDocumentProcessor()
        elif self.mode == "fastest":
            return FastPDFProcessor("pymupdf")
        elif self.mode == "fast":
            return OptimizedDoclingConverter("fast")
        elif self.mode == "balanced":
            return OptimizedDoclingConverter("balanced")
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
    
    def process_document(self, file_path, **kwargs):
        """
        Process a document with the selected method.
        
        Args:
            file_path: Path to document file
            **kwargs: Additional processing options
            
        Returns:
            RAGDocument or processed result
        """
        if hasattr(self.processor, 'process_document'):
            # Hybrid processor
            return self.processor.process_document(file_path, **kwargs)
        elif hasattr(self.processor, 'create_rag_document'):
            # Fast PDF processor
            return self.processor.create_rag_document(file_path, **kwargs)
        else:
            # Docling processor
            conversion_result = self.processor.convert_document(file_path)
            # You'll need to adapt this based on your needs
            return conversion_result
    
    def get_recommendations(self, file_path):
        """Get processing recommendations for a document."""
        if hasattr(self.processor, 'get_processing_recommendations'):
            return self.processor.get_processing_recommendations(file_path)
        else:
            return f"Using {self.mode} mode for {file_path}"
    
    def benchmark(self, file_path):
        """Benchmark different processing methods."""
        if hasattr(self.processor, 'benchmark_all_methods'):
            return self.processor.benchmark_all_methods(file_path)
        else:
            return "Benchmarking only available in hybrid mode"


def main():
    """Quick demo of the document processor."""
    
    print("Enhanced Document Processor")
    print("=" * 40)
    
    # Test file
    test_file = "data/wartsila46f-project-guide.pdf"
    
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        print("Place a PDF in the data/ directory to test.")
        return
    
    print(f"Testing with: {test_file}")
    print()
    
    # Show recommendations
    print("1. Getting Processing Recommendations...")
    processor = DocumentProcessor("auto")
    recommendations = processor.get_recommendations(test_file)
    print(recommendations)
    print()
    
    # Quick processing test
    print("2. Quick Processing Test (Fast Mode)...")
    fast_processor = DocumentProcessor("fastest")
    result = fast_processor.process_document(test_file)
    
    if result:
        metadata = result.metadata if hasattr(result, 'metadata') else result.get('metadata', {})
        print(f"✓ Processed in {metadata.get('processing_time_seconds', 'N/A')} seconds")
        print(f"✓ Extracted {metadata.get('content_length', 'N/A')} characters")
        print(f"✓ Method: {metadata.get('backend', 'N/A')}")
    
    print()
    print("Ready to use! Import from main.py:")
    print("  from main import DocumentProcessor")
    print("  processor = DocumentProcessor('auto')")
    print("  result = processor.process_document('your_file.pdf')")


if __name__ == "__main__":
    main()
