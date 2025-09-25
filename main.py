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
        #if hasattr(self.processor, 'process_document'):
            # Hybrid processor
        # Check for HybridDocumentProcessor specifically to avoid confusion with FastPDFProcessor
        if hasattr(self.processor, 'analyze_document'):
            # Hybrid processor (has both process_document and analyze_document)
            return self.processor.process_document(file_path, **kwargs)
        elif hasattr(self.processor, 'create_rag_document'):
            # Fast PDF processor
            return self.processor.create_rag_document(file_path, **kwargs)
        else:
            # Docling processor
            conversion_result = self.processor.convert_document(file_path)
            
            # Extract metadata with bounding boxes
            document_metadata = self.processor.extract_document_metadata(conversion_result.document)
            content = conversion_result.document.export_to_markdown()
            
            metadata = {
                "file_path": file_path,
                "file_type": os.path.splitext(file_path)[1].lower(),
                "file_size": os.path.getsize(file_path),
                "processing_method": f"docling_{self.processor.mode}",
                "processing_time_seconds": getattr(self.processor, '_last_processing_time', 0),
                **document_metadata  # This includes bounding_boxes and all element data
            }
            
            return {
                'document_id': kwargs.get('document_id', os.path.basename(file_path)),
                'content': content,
                'mime_type': 'text/plain',
                'metadata': metadata
            }
    
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
    print("=" * 40)
    print("1. Getting Processing Recommendations...")
    processor = DocumentProcessor("auto")
    recommendations = processor.get_recommendations(test_file)
    print(recommendations)
    print()
    print("=" * 40)
    print("2. Benchmarking...")
    result = processor.process_document(test_file)
    if result:
        doc_id = result['document_id'] if isinstance(result, dict) else result.document_id
        mime_type = result['mime_type'] if isinstance(result, dict) else result.mime_type  
        metadata = result['metadata'] if isinstance(result, dict) else result.metadata
        content = result['content'] if isinstance(result, dict) else result.content
        
        print(f"Processed document: {doc_id}")
        print(f"Content type: {mime_type}")
        print(f"Metadata keys: {list(metadata.keys())}")
        
        # Check if docling metadata exists (only for Docling processing)
        if 'docling_metadata' in metadata:
            print(f"Has images: {metadata['docling_metadata']['has_images']}")
            print(f"Has tables: {metadata['docling_metadata']['has_tables']}")
            print(f"Page count: {metadata['docling_metadata']['page_count']}")
        else:
            # Fast PDF processor metadata
            print(f"Has tables: {metadata.get('has_tables', 'N/A')}")
            print(f"Page count: {metadata.get('page_count', 'N/A')}")
            print(f"Processing method: {metadata.get('processing_method', 'N/A')}")

        print(f"\nContent preview:\n{content[:500]}...")
    else:
        print("Processing failed - no result returned")


    
    # Quick processing test
    print("=" * 40)
    print("3. Quick Processing Test (Fast Mode)...")
    fast_processor = DocumentProcessor("fastest")
    result = fast_processor.process_document(test_file)
    
    if result:
        metadata = result.metadata if hasattr(result, 'metadata') else result.get('metadata', {})
        print(f"✓ Processed in {metadata.get('processing_time_seconds', 'N/A')} seconds")
        print(f"✓ Extracted {metadata.get('content_length', 'N/A')} characters")
        print(f"✓ Method: {metadata.get('processing_method', metadata.get('backend', 'N/A'))}")
    
    print()
    print("Ready to use! Import from main.py:")
    print("  from main import DocumentProcessor")
    print("  processor = DocumentProcessor('auto')")
    print("  result = processor.process_document('your_file.pdf')")
    
    

    # Test AUTO mode (should use HybridDocumentProcessor)
    print('=== AUTO MODE ===')
    auto_processor = DocumentProcessor('auto')
    auto_result = auto_processor.process_document('data/wartsila46f-project-guide.pdf')
    if auto_result:
        metadata = auto_result.get('metadata', {}) if isinstance(auto_result, dict) else auto_result.metadata
        print('AUTO mode metadata keys:', list(metadata.keys()))
        print('Processing method:', metadata.get('processing_method', 'N/A'))
        
    print()

    # Test BALANCED mode (should use Docling with bounding boxes)
    print('=== BALANCED MODE ===')
    balanced_processor = DocumentProcessor('balanced')
    balanced_result = balanced_processor.process_document('data/wartsila46f-project-guide.pdf')
    if balanced_result:
        print('Balanced result type:', type(balanced_result))
        if hasattr(balanced_result, 'metadata'):
            print('Balanced metadata keys:', list(balanced_result.metadata.keys()))
        elif 'metadata' in balanced_result:
            print('Balanced metadata keys:', list(balanced_result['metadata'].keys()))
        else:
            print('No metadata found in balanced result')


if __name__ == "__main__":
    main()
