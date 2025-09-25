"""
Example usage of the Enhanced Document Processor.

This file demonstrates how to use the EnhancedDocumentProcessor to process
documents with Docling and preserve metadata including bounding boxes.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DOCLING_ACCELERATOR_DEVICE'] = 'cuda'  # or 'auto' for automatic detection

from src.enhanced.enhanced_document_processor import EnhancedDocumentProcessor


def example_basic_usage():
    """Basic usage example."""
    print("=== Basic Usage Example ===")

    # Initialize processor with HTML output
    processor = EnhancedDocumentProcessor(
        output_format='html',
        preserve_images=True,
        preserve_tables=True,
        enable_ocr=False
    )

    # Process a single PDF
    pdf_path = "data/wartsila46f-project-guide.pdf"
    if os.path.exists(pdf_path):
        rag_doc = processor.create_rag_document_from_file(pdf_path)
        print(f"DEBUG: rag_doc type = {type(rag_doc)}")
        if rag_doc:
            # Handle RAGDocument as either dict (from llama_stack_client) or object (fallback)
            doc_id = rag_doc['document_id'] if isinstance(rag_doc, dict) else rag_doc.document_id
            mime_type = rag_doc['mime_type'] if isinstance(rag_doc, dict) else rag_doc.mime_type
            metadata = rag_doc['metadata'] if isinstance(rag_doc, dict) else rag_doc.metadata
            content = rag_doc['content'] if isinstance(rag_doc, dict) else rag_doc.content
            
            print(f"Processed document: {doc_id}")
            print(f"Content type: {mime_type}")
            print(f"Metadata keys: {list(metadata.keys())}")
            print(f"Has images: {metadata['docling_metadata']['has_images']}")
            print(f"Has tables: {metadata['docling_metadata']['has_tables']}")
            print(f"Page count: {metadata['docling_metadata']['page_count']}")

            # Print first 500 characters of content
            print(f"\nContent preview:\n{content[:500]}...")


def example_directory_processing():
    """Process all documents in a directory."""
    print("\n=== Directory Processing Example ===")

    processor = EnhancedDocumentProcessor(output_format='markdown')

    docs_dir = "data/wartsila46f-project-guide.pdf"
    if os.path.exists(docs_dir):
        rag_documents = processor.process_documents_directory(docs_dir)

        print(f"Processed {len(rag_documents)} documents")

        for doc in rag_documents:
            print(f"- {doc.document_id}: {doc.metadata['file_type']} "
                  f"({doc.metadata['docling_metadata']['page_count']} pages)")


def example_chunking():
    """Example of creating chunks for vector database ingestion."""
    print("\n=== Chunking Example ===")

    processor = EnhancedDocumentProcessor(output_format='html')

    pdf_path = "data/wartsila46f-project-guide.pdf"
    if os.path.exists(pdf_path):
        chunks = processor.create_chunks_for_vector_io(pdf_path, chunk_size=1000)

        print(f"Created {len(chunks)} chunks")
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            print(f"\nChunk {i + 1}:")
            print(f"  Content length: {chunk['metadata']['content_length']}")
            print(f"  Chunk type: {chunk['metadata']['chunk_type']}")
            print(f"  Content preview: {chunk['content'][:100]}...")


def example_document_structure():
    """Get detailed document structure information."""
    print("\n=== Document Structure Example ===")

    processor = EnhancedDocumentProcessor(output_format='html')

    pdf_path = "data/wartsila46f-project-guide.pdf"
    if os.path.exists(pdf_path):
        structure = processor.get_document_structure(pdf_path)

        if structure:
            print(f"Document format: {structure['format']}")
            print(f"Total pages: {len(structure['pages'])}")
            print(f"Total elements: {len(structure['elements'])}")

            # Show element types
            element_types = {}
            for element in structure['elements']:
                elem_type = element['type']
                element_types[elem_type] = element_types.get(elem_type, 0) + 1

            print("\nElement types found:")
            for elem_type, count in element_types.items():
                print(f"  {elem_type}: {count}")

            # Show first few elements with bounding boxes
            print("\nFirst few elements with bounding boxes:")
            for element in structure['elements'][:5]:
                print(f"  {element['type']}: bbox={element['bbox']}")


def example_format_comparison():
    """Compare HTML vs Markdown output."""
    print("\n=== Format Comparison Example ===")

    pdf_path = "data/wartsila46f-project-guide.pdf"
    if os.path.exists(pdf_path):
        # HTML format
        html_processor = EnhancedDocumentProcessor(output_format='html')
        html_doc = html_processor.create_rag_document_from_file(pdf_path)

        # Markdown format
        md_processor = EnhancedDocumentProcessor(output_format='markdown')
        md_doc = md_processor.create_rag_document_from_file(pdf_path)

        if html_doc and md_doc:
            print("HTML format:")
            print(f"  MIME type: {html_doc.mime_type}")
            print(f"  Content length: {len(html_doc.content)}")
            print(f"  Content preview: {html_doc.content[:200]}...")

            print("\nMarkdown format:")
            print(f"  MIME type: {md_doc.mime_type}")
            print(f"  Content length: {len(md_doc.content)}")
            print(f"  Content preview: {md_doc.content[:200]}...")


def example_fallback_behavior():
    """Show how the processor handles unsupported formats."""
    print("\n=== Fallback Behavior Example ===")

    processor = EnhancedDocumentProcessor()

    # Try processing an unsupported format
    txt_path = "data/wartsila46f-project-guide.pdf"
    if os.path.exists(txt_path):
        rag_doc = processor.create_rag_document_from_file(txt_path)
        if rag_doc:
            metadata = rag_doc['metadata'] if isinstance(rag_doc, dict) else rag_doc.metadata
            content = rag_doc['content'] if isinstance(rag_doc, dict) else rag_doc.content
            print(f"Fallback processing for {metadata['file_type']}")
            print(f"Processing method: {metadata['processing_method']}")
            print(f"Content length: {len(content)}")


if __name__ == "__main__":
    print("Enhanced Document Processor Examples")
    print("=" * 40)

    # Run examples (comment out ones you don't want to test)
    example_basic_usage()
    # example_directory_processing()
    example_chunking()
    # example_document_structure()
    # example_format_comparison()
    # example_fallback_behavior()

    print("\n" + "=" * 40)
    print("Examples completed!")
