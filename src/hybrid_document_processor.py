"""
Hybrid Document Processor combining fast and feature-rich processing modes.

This processor automatically selects the best processing method based on requirements
and provides multiple processing strategies for different use cases.
"""

import time
import os
from typing import Optional, Dict, Any, List, Literal
from pathlib import Path

from optimized_docling_converter import OptimizedDoclingConverter
from fast_pdf_processor import FastPDFProcessor

try:
    from llama_stack_client import RAGDocument
except ImportError:
    class RAGDocument:
        def __init__(self, document_id: str, content: Any, mime_type: str, metadata: Optional[Dict] = None):
            self.document_id = document_id
            self.content = content
            self.mime_type = mime_type
            self.metadata = metadata or {}


class HybridDocumentProcessor:
    """Intelligent document processor that selects optimal processing method."""
    
    def __init__(self):
        """Initialize hybrid processor with all available backends."""
        self.fast_processor = None
        self.docling_processors = {}
        
        # Initialize fast processors if available
        try:
            self.fast_processor = FastPDFProcessor("pymupdf")
        except ImportError:
            try:
                self.fast_processor = FastPDFProcessor("pdfplumber")
            except ImportError:
                print("Warning: No fast PDF processors available. Install PyMuPDF or pdfplumber.")
        
        # Initialize Docling processors for different modes
        for mode in ["fastest", "fast", "balanced", "quality"]:
            try:
                self.docling_processors[mode] = OptimizedDoclingConverter(mode)
            except Exception as e:
                print(f"Warning: Could not initialize Docling {mode} mode: {e}")

    def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """Analyze document to recommend optimal processing method."""
        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Quick page count estimation (for PDFs)
        page_count = 0
        if file_ext == '.pdf' and self.fast_processor:
            try:
                result = self.fast_processor.process_document(file_path)
                page_count = result.get('page_count', 0)
                fast_time = result.get('processing_time_seconds', 0)
            except:
                page_count = max(1, file_size // 100000)  # Rough estimate
                fast_time = 1.0
        
        # Processing recommendations
        recommendations = {
            "file_info": {
                "size_mb": file_size / 1024 / 1024,
                "pages": page_count,
                "type": file_ext
            },
            "recommendations": {}
        }
        
        # Text-only scenarios
        recommendations["recommendations"]["text_only"] = {
            "method": "fast_pdf",
            "estimated_time": f"{fast_time:.1f}s" if 'fast_time' in locals() else "5-10s",
            "features": ["Text extraction"],
            "use_case": "Search indexing, basic analysis"
        }
        
        # Structured processing
        if page_count < 50:
            recommendations["recommendations"]["structured"] = {
                "method": "docling_fast",
                "estimated_time": f"{page_count * 2}s",
                "features": ["Text", "Tables", "Structure"],
                "use_case": "Document analysis with structure"
            }
        elif page_count < 200:
            recommendations["recommendations"]["structured"] = {
                "method": "docling_fastest",
                "estimated_time": f"{page_count * 1}s",
                "features": ["Text", "Basic structure"],
                "use_case": "Large document processing"
            }
        
        # Full featured processing
        if page_count < 20:
            recommendations["recommendations"]["full_featured"] = {
                "method": "docling_balanced",
                "estimated_time": f"{page_count * 5}s",
                "features": ["Text", "Tables", "Images", "Layout"],
                "use_case": "Complete document understanding"
            }
        
        return recommendations

    def process_document(self, 
                        file_path: str,
                        mode: Literal["auto", "fastest", "text_only", "fast", "balanced", "quality"] = "auto",
                        document_id: Optional[str] = None) -> Optional[RAGDocument]:
        """
        Process document with selected or auto-detected optimal method.
        
        Args:
            file_path: Path to document
            mode: Processing mode
                - "auto": Automatically select best method
                - "fastest": Use fastest available method  
                - "text_only": Fast text extraction only
                - "fast": Fast Docling processing
                - "balanced": Balanced Docling processing
                - "quality": Full quality Docling processing
            document_id: Optional document ID
        """
        start_time = time.time()
        
        if document_id is None:
            document_id = os.path.basename(file_path)
        
        # Auto mode selection
        if mode == "auto":
            analysis = self.analyze_document(file_path)
            file_size_mb = analysis["file_info"]["size_mb"]
            page_count = analysis["file_info"]["pages"]
            
            if page_count > 100 or file_size_mb > 50:
                mode = "fastest"
            elif page_count > 50:
                mode = "fast"
            else:
                mode = "balanced"
        
        # Process based on selected mode
        try:
            if mode == "text_only" or mode == "fastest":
                if self.fast_processor:
                    result = self.fast_processor.create_rag_document(file_path, document_id)
                    if result:
                        result.metadata["auto_selected_mode"] = mode
                        result.metadata["total_processing_time"] = time.time() - start_time
                        return result
                # Fallback to docling fastest
                mode = "fastest"
            
            # Use Docling for structured processing
            if mode in self.docling_processors:
                processor = self.docling_processors[mode]
                conversion_result = processor.convert_document(file_path)
                
                # Create RAGDocument
                content = conversion_result.document.export_to_markdown()
                
                metadata = {
                    "file_path": file_path,
                    "file_type": os.path.splitext(file_path)[1].lower(),
                    "file_size": os.path.getsize(file_path),
                    "processing_method": f"docling_{mode}",
                    "processing_mode": mode,
                    "total_processing_time": time.time() - start_time,
                    "page_count": len(conversion_result.document.pages),
                    "docling_mode_info": processor.get_processing_info()
                }
                
                return RAGDocument(
                    document_id=document_id,
                    content=content,
                    mime_type="text/plain",
                    metadata=metadata
                )
        
        except Exception as e:
            print(f"Error processing {file_path} with mode {mode}: {e}")
            
            # Final fallback to text-only if available
            if self.fast_processor and mode != "text_only":
                try:
                    result = self.fast_processor.create_rag_document(file_path, document_id)
                    if result:
                        result.metadata["fallback_mode"] = "text_only"
                        result.metadata["original_mode_error"] = str(e)
                        return result
                except Exception as fallback_error:
                    print(f"Fallback processing also failed: {fallback_error}")
        
        return None

    def benchmark_all_methods(self, file_path: str) -> Dict[str, Any]:
        """Benchmark all available processing methods on a document."""
        results = {}
        
        # Test fast processing
        if self.fast_processor:
            try:
                start = time.time()
                result = self.fast_processor.process_document(file_path)
                results["fast_pdf"] = {
                    "time": time.time() - start,
                    "success": "error" not in result,
                    "content_length": result.get("content_length", 0),
                    "method": self.fast_processor.backend
                }
            except Exception as e:
                results["fast_pdf"] = {"error": str(e)}
        
        # Test Docling modes
        for mode in ["fastest", "fast", "balanced"]:
            if mode in self.docling_processors:
                try:
                    start = time.time()
                    processor = self.docling_processors[mode]
                    conversion_result = processor.convert_document(file_path)
                    content = conversion_result.document.export_to_markdown()
                    
                    results[f"docling_{mode}"] = {
                        "time": time.time() - start,
                        "success": True,
                        "content_length": len(content),
                        "pages": len(conversion_result.document.pages),
                        "mode_info": processor.get_processing_info()
                    }
                except Exception as e:
                    results[f"docling_{mode}"] = {"error": str(e)}
        
        return results

    def get_processing_recommendations(self, file_path: str) -> str:
        """Get human-readable processing recommendations."""
        analysis = self.analyze_document(file_path)
        
        output = []
        output.append(f"Document Analysis: {os.path.basename(file_path)}")
        output.append("=" * 50)
        
        file_info = analysis["file_info"]
        output.append(f"Size: {file_info['size_mb']:.1f} MB")
        output.append(f"Pages: {file_info['pages']}")
        output.append(f"Type: {file_info['type']}")
        output.append("")
        
        output.append("Recommended Processing Methods:")
        output.append("-" * 30)
        
        for name, rec in analysis["recommendations"].items():
            output.append(f"{name.title().replace('_', ' ')}:")
            output.append(f"  Method: {rec['method']}")
            output.append(f"  Estimated time: {rec['estimated_time']}")
            output.append(f"  Features: {', '.join(rec['features'])}")
            output.append(f"  Use case: {rec['use_case']}")
            output.append("")
        
        return "\n".join(output)


if __name__ == "__main__":
    # Demo the hybrid processor
    pdf_path = "data/wartsila46f-project-guide.pdf"
    
    if os.path.exists(pdf_path):
        processor = HybridDocumentProcessor()
        
        print("Hybrid Document Processor Demo")
        print("=" * 40)
        
        # Show recommendations
        print(processor.get_processing_recommendations(pdf_path))
        
        # Quick benchmark
        print("\nQuick Benchmark:")
        print("-" * 20)
        
        # Test fastest mode
        result = processor.process_document(pdf_path, mode="fastest")
        if result:
            metadata = result.metadata if hasattr(result, 'metadata') else result['metadata']
            print(f"Fastest mode: {metadata['total_processing_time']:.2f}s")
            print(f"Method: {metadata['processing_method']}")
    else:
        print(f"Test file not found: {pdf_path}")
        print("Place a PDF in the data/ directory to test.")
