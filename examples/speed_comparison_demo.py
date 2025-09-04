"""
Speed Comparison Demo - Fast vs Current Docling Processing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from src.fast_pdf_processor import FastPDFProcessor
from src.enhanced_document_processor import EnhancedDocumentProcessor

def compare_processing_speeds():
    """Compare processing speeds between fast and current methods."""
    pdf_path = "data/wartsila46f-project-guide.pdf"
    
    print("Document Processing Speed Comparison")
    print("=" * 50)
    print(f"Test file: {pdf_path}")
    print()
    
    # Fast PyMuPDF processing
    print("1. Fast PyMuPDF Processing (Text Only)")
    print("-" * 40)
    fast_processor = FastPDFProcessor("pymupdf")
    
    start_time = time.time()
    fast_result = fast_processor.process_document(pdf_path)
    fast_time = time.time() - start_time
    
    print(f"Processing time: {fast_time:.2f} seconds")
    print(f"Pages processed: {fast_result.get('page_count', 0)}")
    print(f"Content extracted: {fast_result.get('content_length', 0):,} characters")
    print()
    
    # pdfplumber processing (with tables)
    print("2. pdfplumber Processing (Text + Tables)")
    print("-" * 40)
    table_processor = FastPDFProcessor("pdfplumber")
    
    start_time = time.time()
    table_result = table_processor.process_document(pdf_path)
    table_time = time.time() - start_time
    
    print(f"Processing time: {table_time:.2f} seconds")
    print(f"Pages processed: {table_result.get('page_count', 0)}")
    print(f"Tables found: {len(table_result.get('tables', []))}")
    print(f"Content extracted: {table_result.get('content_length', 0):,} characters")
    print()
    
    # Original Docling processing (we'll estimate based on your results)
    print("3. Original Docling Processing (Full Features)")
    print("-" * 40)
    original_time = 368  # From your terminal output
    print(f"Processing time: {original_time} seconds ({original_time/60:.1f} minutes)")
    print("Features: Text + Tables + Images + Layout + Metadata")
    print()
    
    # Speed comparisons
    print("Speed Improvement Analysis")
    print("=" * 50)
    print(f"PyMuPDF vs Original Docling:")
    print(f"  Speed improvement: {original_time/fast_time:.1f}x faster")
    print(f"  Time saved: {original_time - fast_time:.1f} seconds")
    print()
    
    print(f"pdfplumber vs Original Docling:")
    print(f"  Speed improvement: {original_time/table_time:.1f}x faster")
    print(f"  Time saved: {original_time - table_time:.1f} seconds")
    print()
    
    # Recommendations
    print("Recommendations by Use Case")
    print("=" * 50)
    print("For TEXT SEARCH/INDEXING:")
    print(f"  → Use PyMuPDF ({fast_time:.1f}s vs {original_time}s)")
    print(f"  → {original_time/fast_time:.0f}x faster, perfect for search engines")
    print()
    
    print("For DOCUMENT ANALYSIS WITH TABLES:")
    print(f"  → Use pdfplumber ({table_time:.1f}s vs {original_time}s)")
    print(f"  → {original_time/table_time:.0f}x faster, extracts {len(table_result.get('tables', []))} tables")
    print()
    
    print("For COMPLETE DOCUMENT UNDERSTANDING:")
    print(f"  → Use optimized Docling (estimated 60-120s vs {original_time}s)")
    print(f"  → 3-6x faster while keeping images and layout")


if __name__ == "__main__":
    compare_processing_speeds()
