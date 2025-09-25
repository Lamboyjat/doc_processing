"""
Dynamic comparison of actual performance and features across Docling optimization modes.
"""
import sys
import os
import time
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable GPU warnings for CPU-only processing
os.environ['DOCLING_CPU_ONLY'] = '1'

try:
    from src.core.optimized_docling_converter import OptimizedDoclingConverter
    DOCLING_AVAILABLE = True
except ImportError as e:
    print(f"Docling not available: {e}")
    print("Showing theoretical comparison instead.")
    DOCLING_AVAILABLE = False

def measure_mode_performance(pdf_path: str):
    """Measure actual performance and feature extraction for each Docling mode."""
    
    print("Dynamic Docling Mode Performance Comparison")
    print("=" * 60)
    print(f"Test file: {pdf_path}")
    print(f"File exists: {Path(pdf_path).exists()}")
    print()
    
    if not Path(pdf_path).exists():
        print(f"ERROR: Test file not found: {pdf_path}")
        print("Please ensure you have a PDF file in the data/ directory.")
        return
    
    modes = ["fastest", "fast", "balanced", "quality"]
    results = {}
    
    # Test each mode
    for mode in modes:
        print(f"Testing {mode.upper()} mode...")
        print("-" * 30)
        
        try:
            # Create converter and do single conversion
            converter = OptimizedDoclingConverter(mode)
            start_time = time.time()
            conversion_result = converter.convert_document(pdf_path)
            processing_time = time.time() - start_time
            
            if conversion_result and conversion_result.document:
                # Get detailed metadata
                metadata = converter.extract_document_metadata(conversion_result.document)
                content = conversion_result.document.export_to_markdown()
                
                results[mode] = {
                    "processing_time": processing_time,
                    "pages_processed": len(conversion_result.document.pages),
                    "tables_found": len(metadata.get("tables", [])),
                    "images_found": len(metadata.get("images", [])),
                    "has_bounding_boxes": len(metadata.get("bounding_boxes", {})) > 0,
                    "bbox_count": len(metadata.get("bounding_boxes", {})),
                    "content_length": len(content),
                    "elements_by_type": metadata.get("elements_by_type", {}),
                    "summary": metadata.get("summary", {}),
                    "success": True
                }
                
                # Print immediate results
                print(f" Processing time: {results[mode]['processing_time']:.2f}s ({results[mode]['processing_time']/60:.1f} minutes)")
                print(f" Pages processed: {results[mode]['pages_processed']} pages")
                print(f" Tables found: {results[mode]['tables_found']} tables")
                print(f" Images found: {results[mode]['images_found']}")
                print(f" Bounding boxes: {results[mode]['bbox_count']} elements")
                print(f" Content length: {results[mode]['content_length']:,} characters")
                print(f" Elements: {results[mode]['summary']}")
                
                # Debug: Test the classify function directly
                print(f"  Debug: Document type: {type(conversion_result.document)}")
                print(f"  Debug: Document has {len(conversion_result.document.pages)} pages")
                
                # Test classification of first few items
                print(f"  Debug: Testing classification of first few items:")
                item_count = 0
                picture_count = 0
                table_count = 0
                text_count = 0
                
                for item, level in conversion_result.document.iterate_items():
                    if item_count < 10:  # Show first 10 items
                        item_type = type(item).__name__
                        has_prov = hasattr(item, 'prov') and item.prov
                        
                        # Test if it's a picture
                        is_picture = "PictureItem" in item_type
                        # Test if it's a table  
                        is_table = "TableItem" in item_type
                        # Test if it's text
                        is_text = "TextItem" in item_type
                        
                        # Get the text content from the item
                        item_text = getattr(item, 'text', '') or ''
                        text_preview = item_text[:50] + "..." if len(item_text) > 50 else item_text
                        print(f"    Item {item_count}: {item_type}, picture={is_picture}, table={is_table}, text={is_text}, has_prov={has_prov}")
                        if item_text:
                            print(f"      Content: '{text_preview}'")
                        
                        if is_picture:
                            picture_count += 1
                        elif is_table:
                            table_count += 1
                        elif is_text:
                            text_count += 1
                    
                    item_count += 1
                    if item_count >= 200:  # Count more items
                        break
                        
                print(f"  Debug: From first 200 items - Pictures: {picture_count}, Tables: {table_count}, Text: {text_count}")
                print(f"  Debug: Total items counted: {item_count}")
                
            else:
                results[mode] = {
                    "success": False,
                    "error": "Conversion failed - no document returned"
                }
                print(f" Failed: {results[mode]['error']}")
                
        except Exception as e:
            results[mode] = {
                "success": False,
                "error": str(e)
            }
            print(f" Exception: {e}")
        
        print()
    
    # Print comparison table
    print("PERFORMANCE COMPARISON TABLE")
    print("=" * 80)
    
    # Header
    header = f"{'Metric':<20} | {'Fastest':<12} | {'Fast':<12} | {'Balanced':<12} | {'Quality':<12}"
    print(header)
    print("-" * len(header))
    
    # Metrics to compare
    metrics = [
        ("Processing Time", "processing_time", "s", ".2f"),
        ("Pages Processed", "pages_processed", "", "d"),
        ("Tables Found", "tables_found", "", "d"),
        ("Images Found", "images_found", "", "d"),
        ("Bounding Boxes", "bbox_count", "", "d"),
        ("Content Length", "content_length", " chars", ",d")
    ]
    
    for metric_name, key, suffix, fmt in metrics:
        row = f"{metric_name:<20} |"
        for mode in modes:
            if results.get(mode, {}).get("success"):
                value = results[mode].get(key, 0)
                if fmt == ",d":
                    formatted = f"{value:,}{suffix}"
                elif fmt == ".2f":
                    formatted = f"{value:.2f}{suffix}"
                else:
                    formatted = f"{value}{suffix}"
                row += f" {formatted:<11} |"
            else:
                row += f" {'ERROR':<11} |"
        print(row)
    
    print()
    
    # Speed comparison
    print("SPEED COMPARISON")
    print("=" * 30)
    fastest_time = results.get("fastest", {}).get("processing_time", 0)
    if fastest_time > 0:
        for mode in modes[1:]:  # Skip fastest as baseline
            if results.get(mode, {}).get("success"):
                mode_time = results[mode]["processing_time"]
                slowdown = mode_time / fastest_time
                print(f"{mode} vs fastest: {slowdown:.1f}x slower ({mode_time:.2f}s vs {fastest_time:.2f}s)")
    
    print()
    
    # Feature preservation analysis
    print("FEATURE PRESERVATION ANALYSIS")
    print("=" * 40)
    for mode in modes:
        if results.get(mode, {}).get("success"):
            r = results[mode]
            print(f"\n{mode.upper()} MODE:")
            print(f"  Time: {r['processing_time']:.2f}s")
            print(f"  Text extraction: YES ({r['content_length']:,} chars)")
            print(f"  Table detection: {'YES' if r['tables_found'] > 0 else 'NO'} ({r['tables_found']} found)")
            print(f"  Image extraction: {'YES' if r['images_found'] > 0 else 'NO'} ({r['images_found']} found)")
            print(f"  Bounding boxes: {'YES' if r['has_bounding_boxes'] else 'NO'} ({r['bbox_count']} elements)")
            print(f"  Elements found: {r['elements_by_type']}")
    
    return results


def show_usage_recommendations(results):
    """Show usage recommendations based on actual measurements."""
    
    print("USAGE RECOMMENDATIONS")
    print("=" * 40)
    
    if not any(r.get("success") for r in results.values()):
        print("No successful results to analyze.")
        return
    
    # Find fastest mode that worked
    fastest_working = None
    for mode in ["fastest", "fast", "balanced", "quality"]:
        if results.get(mode, {}).get("success"):
            fastest_working = mode
            break
    
    if fastest_working:
        base_time = results[fastest_working]["processing_time"]
        
        print("FOR TEXT SEARCH/INDEXING:")
        print(f"  → Use {fastest_working.upper()} mode ({base_time:.2f}s)")
        print(f"  → Gets {results[fastest_working]['content_length']:,} chars of text")
        print()
        
        print("FOR DOCUMENT ANALYSIS WITH TABLES:")
        for mode in ["fast", "balanced", "quality"]:
            if results.get(mode, {}).get("success") and results[mode]["tables_found"] > 0:
                time_ratio = results[mode]["processing_time"] / base_time
                print(f"  → Use {mode.upper()} mode ({results[mode]['processing_time']:.2f}s, {time_ratio:.1f}x slower)")
                print(f"  → Extracts {results[mode]['tables_found']} tables")
                break
        print()
        
        print("FOR COMPLETE DOCUMENT UNDERSTANDING:")
        for mode in ["balanced", "quality"]:
            if results.get(mode, {}).get("success"):
                time_ratio = results[mode]["processing_time"] / base_time
                print(f"  → Use {mode.upper()} mode ({results[mode]['processing_time']:.2f}s, {time_ratio:.1f}x slower)")
                print(f"  → Gets tables: {results[mode]['tables_found']}, images: {results[mode]['images_found']}")
                print(f"  → Bounding boxes: {results[mode]['bbox_count']} elements")
                break


if __name__ == "__main__":
    # Test with default PDF or user-specified file
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "data/wartsila46f-project-guide.pdf" #"data/Alfa Laval LKH.pdf"
    
    results = measure_mode_performance(pdf_path)
    
    if results:
        show_usage_recommendations(results)
