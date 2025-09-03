"""
Migration Guide: From DocumentProcessor to EnhancedDocumentProcessor

This file shows how to migrate your existing DocumentProcessor code to use
the EnhancedDocumentProcessor with Docling for better extraction and metadata preservation.
"""

# =============================================================================
# BEFORE: Your Original DocumentProcessor Usage
# =============================================================================

"""
# Original usage
from your_module import DocumentProcessor

processor = DocumentProcessor()

# Process single file
rag_doc = processor.create_rag_document_from_file('document.pdf')
print(f"Content: {rag_doc.content}")  # Plain text only
print(f"Pages: {rag_doc.metadata.get('pages', 'Unknown')}")  # Limited metadata

# Process directory
documents = processor.process_documents_directory('./docs/')

# Create chunks
chunks = processor.create_chunks_for_vector_io('document.pdf', chunk_size=1000)
"""

# =============================================================================
# AFTER: Enhanced DocumentProcessor with Docling
# =============================================================================

from enhanced_document_processor import EnhancedDocumentProcessor

def migrate_basic_usage():
    """Migrated basic usage with enhanced features."""
    print("=== Migrated Basic Usage ===")

    # Initialize with enhanced options
    processor = EnhancedDocumentProcessor(
        output_format='html',  # NEW: Choose output format
        preserve_images=True,  # NEW: Extract images
        preserve_tables=True,  # NEW: Preserve table structure
        enable_ocr=False       # NEW: Enable OCR for scanned docs
    )

    # Process single file - SAME API, enhanced results
    rag_doc = processor.create_rag_document_from_file('data/Alfa Laval LKH.pdf')

    if rag_doc:
        # Handle RAGDocument as either dict (from llama_stack_client) or object (fallback)
        content = rag_doc['content'] if isinstance(rag_doc, dict) else rag_doc.content
        mime_type = rag_doc['mime_type'] if isinstance(rag_doc, dict) else rag_doc.mime_type
        metadata = rag_doc['metadata'] if isinstance(rag_doc, dict) else rag_doc.metadata
        
        print(f"Content: {content[:200]}...")  # HTML/Markdown with structure
        print(f"Format: {mime_type}")  # text/html or text/plain

        # ENHANCED METADATA
        print(f"Pages: {metadata['docling_metadata']['page_count']}")
        print(f"Has images: {metadata['docling_metadata']['has_images']}")
        print(f"Has tables: {metadata['docling_metadata']['has_tables']}")
        print(f"Processing method: {metadata['processing_method']}")  # 'docling'

def migrate_directory_processing():
    """Migrated directory processing."""
    print("\n=== Migrated Directory Processing ===")

    processor = EnhancedDocumentProcessor(output_format='markdown')

    # SAME API, enhanced processing
    documents = processor.process_documents_directory('./docs/')

    for doc in documents:
        # Handle RAGDocument as either dict or object
        doc_id = doc['document_id'] if isinstance(doc, dict) else doc.document_id
        doc_metadata = doc['metadata'] if isinstance(doc, dict) else doc.metadata
        
        print(f"Processed: {doc_id}")
        print(f"  Format: {doc_metadata['output_format']}")
        print(f"  Pages: {doc_metadata['docling_metadata']['page_count']}")
        print(f"  File type: {doc_metadata['file_type']}")

def migrate_chunking():
    """Migrated chunking with enhanced metadata."""
    print("\n=== Migrated Chunking ===")

    processor = EnhancedDocumentProcessor()

    # SAME API, enhanced chunking
    chunks = processor.create_chunks_for_vector_io('data/Alfa Laval LKH.pdf', chunk_size=1000)

    for i, chunk in enumerate(chunks[:3]):  # Show first 3
        print(f"Chunk {i+1}:")
        print(f"  Type: {chunk['metadata']['chunk_type']}")
        print(f"  Length: {chunk['metadata']['content_length']}")
        print(f"  MIME: {chunk['mime_type']}")
        print(f"  Content: {chunk['content'][:100]}...")

def demonstrate_new_features():
    """Show new features available in enhanced processor."""
    print("\n=== New Features ===")

    processor = EnhancedDocumentProcessor()

    # NEW: Get detailed document structure
    structure = processor.get_document_structure('data/Alfa Laval LKH.pdf')
    if structure:
        print("Document Structure:")
        print(f"  Format: {structure['format']}")
        print(f"  Total pages: {len(structure['pages'])}")
        print(f"  Total elements: {len(structure['elements'])}")

        # Show element types
        element_types = {}
        for element in structure['elements']:
            elem_type = element['type']
            element_types[elem_type] = element_types.get(elem_type, 0) + 1

        print("  Element breakdown:")
        for elem_type, count in element_types.items():
            print(f"    {elem_type}: {count}")

def compare_formats():
    """Compare HTML vs Markdown output."""
    print("\n=== Format Comparison ===")

    # HTML format
    html_processor = EnhancedDocumentProcessor(output_format='html')
    html_doc = html_processor.create_rag_document_from_file('data/Alfa Laval LKH.pdf')

    # Markdown format
    md_processor = EnhancedDocumentProcessor(output_format='markdown')
    md_doc = md_processor.create_rag_document_from_file('data/Alfa Laval LKH.pdf')

    if html_doc and md_doc:
        # Handle RAGDocument as either dict or object
        html_content = html_doc['content'] if isinstance(html_doc, dict) else html_doc.content
        html_mime = html_doc['mime_type'] if isinstance(html_doc, dict) else html_doc.mime_type
        md_content = md_doc['content'] if isinstance(md_doc, dict) else md_doc.content
        md_mime = md_doc['mime_type'] if isinstance(md_doc, dict) else md_doc.mime_type
        
        print("HTML Output:")
        print(f"  MIME: {html_mime}")
        print(f"  Length: {len(html_content)}")
        print(f"  Preview: {html_content[:100]}...")

        print("\nMarkdown Output:")
        print(f"  MIME: {md_mime}")
        print(f"  Length: {len(md_content)}")
        print(f"  Preview: {md_content[:100]}...")

# =============================================================================
# CONFIGURATION EXAMPLES
# =============================================================================

def configuration_examples():
    """Show different configuration options."""
    print("\n=== Configuration Examples ===")

    # Basic configuration
    basic = EnhancedDocumentProcessor()

    # Full-featured configuration
    full_featured = EnhancedDocumentProcessor(
        output_format='html',
        preserve_images=True,
        preserve_tables=True,
        enable_ocr=True
    )

    # Lightweight configuration
    lightweight = EnhancedDocumentProcessor(
        output_format='markdown',
        preserve_images=False,
        preserve_tables=False,
        enable_ocr=False
    )

    print("Available configurations:")
    print("  Basic: HTML output, images/tables preserved, no OCR")
    print("  Full-featured: HTML output, all features enabled")
    print("  Lightweight: Markdown output, minimal processing")

# =============================================================================
# ERROR HANDLING EXAMPLES
# =============================================================================

def error_handling_examples():
    """Show enhanced error handling."""
    print("\n=== Error Handling ===")

    processor = EnhancedDocumentProcessor()

    try:
        # This will work with Docling
        doc = processor.create_rag_document_from_file('data/Alfa Laval LKH.pdf')
        print("✅ Docling processing successful")

    except Exception as e:
        print(f"❌ Docling failed: {e}")

        # The processor will automatically fall back to basic extraction
        print("🔄 Falling back to basic extraction...")

        # This would use the fallback method
        doc = processor.create_rag_document_from_file('data/Alfa Laval LKH.pdf')
        if doc:
            doc_metadata = doc['metadata'] if isinstance(doc, dict) else doc.metadata
            print(f"✅ Fallback successful: {doc_metadata['processing_method']}")

# =============================================================================
# INTEGRATION PATTERNS
# =============================================================================

def integration_patterns():
    """Show how to integrate with existing RAG pipelines."""
    print("\n=== Integration Patterns ===")

    processor = EnhancedDocumentProcessor(output_format='html')

    # Pattern 1: Process and chunk for vector database
    def process_for_vector_db(file_path: str):
        """Process document and prepare chunks for vector database."""
        # Create document with enhanced metadata
        doc = processor.create_rag_document_from_file(file_path)

        if doc:
            # Create intelligent chunks
            chunks = processor.create_chunks_for_vector_io(file_path, chunk_size=800)

            return {
                'document': doc,
                'chunks': chunks,
                'metadata': {
                    'total_chunks': len(chunks),
                    'has_images': (doc['metadata'] if isinstance(doc, dict) else doc.metadata)['docling_metadata']['has_images'],
                    'has_tables': (doc['metadata'] if isinstance(doc, dict) else doc.metadata)['docling_metadata']['has_tables']
                }
            }

    # Pattern 2: Batch processing with progress tracking
    def batch_process_documents(file_paths: list):
        """Process multiple documents with progress tracking."""
        results = []
        for i, file_path in enumerate(file_paths):
            print(f"Processing {i+1}/{len(file_paths)}: {file_path}")
            result = process_for_vector_db(file_path)
            if result:
                results.append(result)

        return results

    print("Integration patterns available:")
    print("  1. process_for_vector_db(): Process single document with chunks")
    print("  2. batch_process_documents(): Process multiple documents")

if __name__ == "__main__":
    print("Enhanced Document Processor - Migration Guide")
    print("=" * 50)

    # Run migration examples
    migrate_basic_usage()
    migrate_directory_processing()
    migrate_chunking()
    demonstrate_new_features()
    compare_formats()
    configuration_examples()
    error_handling_examples()
    integration_patterns()

    print("\n" + "=" * 50)
    print("Migration guide completed!")
    print("\nKey takeaways:")
    print("✅ Same API, enhanced capabilities")
    print("✅ Preserved bounding boxes and metadata")
    print("✅ Multiple output formats (HTML/Markdown)")
    print("✅ Intelligent chunking")
    print("✅ Robust error handling with fallbacks")
