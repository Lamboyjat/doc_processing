"""
Detailed comparison of what features are preserved in each Docling optimization mode.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.optimized_docling_converter import OptimizedDoclingConverter

def show_feature_comparison():
    """Show detailed feature comparison across all Docling modes."""
    
    print("Optimized Docling Feature Preservation Comparison")
    print("=" * 60)
    print()
    
    # Feature matrix
    features = {
        "Text Extraction": {
            "fastest": "✓ Full text content",
            "fast": "✓ Full text content", 
            "balanced": "✓ Full text content",
            "quality": "✓ Full text content"
        },
        "Document Structure": {
            "fastest": "✓ Basic paragraphs/headings",
            "fast": "✓ Structured elements",
            "balanced": "✓ Full document structure", 
            "quality": "✓ Full document structure"
        },
        "Table Detection": {
            "fastest": "✗ No table detection",
            "fast": "✓ Fast table detection",
            "balanced": "✓ Accurate table detection",
            "quality": "✓ Highest accuracy tables"
        },
        "Table Cell Matching": {
            "fastest": "✗ No cell matching",
            "fast": "✓ Basic cell relationships",
            "balanced": "✓ Full cell relationships",
            "quality": "✓ Precise cell matching"
        },
        "Table Images": {
            "fastest": "✗ No table images",
            "fast": "✗ No table images",
            "balanced": "✓ Table screenshots",
            "quality": "✓ High-quality table images"
        },
        "Picture/Image Extraction": {
            "fastest": "✗ No images extracted",
            "fast": "✗ No images extracted",
            "balanced": "✓ All images with metadata",
            "quality": "✓ All images with metadata"
        },
        "Bounding Boxes": {
            "fastest": "✓ Text element positions",
            "fast": "✓ Text + table positions",
            "balanced": "✓ All element positions",
            "quality": "✓ Precise positioning"
        },
        "OCR for Scanned Content": {
            "fastest": "✗ No OCR",
            "fast": "✗ No OCR",
            "balanced": "✗ No OCR",
            "quality": "✓ Full OCR processing"
        },
        "Page Layout": {
            "fastest": "✓ Basic layout info",
            "fast": "✓ Enhanced layout",
            "balanced": "✓ Complete layout",
            "quality": "✓ Detailed layout analysis"
        },
        "Metadata Preservation": {
            "fastest": "✓ Basic metadata",
            "fast": "✓ Enhanced metadata",
            "balanced": "✓ Rich metadata",
            "quality": "✓ Complete metadata"
        }
    }
    
    # Print comparison table
    modes = ["fastest", "fast", "balanced", "quality"]
    
    # Header
    print(f"{'Feature':<25} | {'Fastest':<20} | {'Fast':<20} | {'Balanced':<20} | {'Quality':<20}")
    print("-" * 110)
    
    # Features
    for feature, mode_data in features.items():
        row = f"{feature:<25} |"
        for mode in modes:
            row += f" {mode_data[mode]:<19} |"
        print(row)
    
    print()
    print("Performance vs Features Trade-off")
    print("=" * 40)
    
    for mode in modes:
        processor = OptimizedDoclingConverter(mode)
        info = processor.get_processing_info()
        print(f"\n{mode.upper()} MODE:")
        print(f"  Speed: {info['speed']}")
        print(f"  Features: {', '.join(info['features'])}")
        print(f"  Best for: {info['use_case']}")
    
    print()
    print("What You LOSE by optimizing:")
    print("-" * 30)
    print("fastest → fast: No table detection")
    print("fast → balanced: No images, no table images")  
    print("balanced → quality: No OCR for scanned documents")
    
    print()
    print("What You KEEP in each mode:")
    print("-" * 30)
    print("fastest: Text content, basic structure, bounding boxes")
    print("fast: + Tables with cell relationships") 
    print("balanced: + Images, table images, complete layout")
    print("quality: + OCR for scanned content")


def demonstrate_preserved_content():
    """Show what content is actually preserved in practice."""
    
    pdf_path = "data/wartsila46f-project-guide.pdf"
    
    print("\nPractical Content Preservation Demo")
    print("=" * 40)
    
    try:
        # Test fastest mode
        processor = OptimizedDoclingConverter("fastest")
        result = processor.convert_document(pdf_path)
        
        # Count elements
        text_elements = 0
        for item, _ in result.document.iterate_items():
            if hasattr(item, 'text') and item.text:
                text_elements += 1
        
        print(f"FASTEST MODE Results:")
        print(f"  Pages: {len(result.document.pages)}")
        print(f"  Text elements: {text_elements}")
        print(f"  Document structure: {type(result.document)}")
        print(f"  Bounding boxes: {'✓' if any(hasattr(item, 'prov') for item, _ in result.document.iterate_items()) else '✗'}")
        
        # Export sample
        content = result.document.export_to_markdown()
        print(f"  Content length: {len(content):,} characters")
        print(f"  Sample: {content[:200]}...")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        print("(Requires Docling installation in virtual environment)")


if __name__ == "__main__":
    show_feature_comparison()
    demonstrate_preserved_content()
