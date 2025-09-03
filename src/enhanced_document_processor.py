"""
Enhanced Document Processor using Docling.

This module provides an enhanced version of document processing that uses Docling
for better extraction of text, images, tables, and metadata preservation including
bounding boxes. Supports output in HTML and Markdown formats while maintaining
compatibility with the original DocumentProcessor interface.
"""

import os
import base64
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

try:
    from llama_stack_client import RAGDocument
except ImportError:
    # Fallback for when llama_stack_client is not available
    print("WARNING: llama_stack_client is not available, install it to use RAGDocument")
    class RAGDocument:
        def __init__(self, document_id: str, content: Any, mime_type: str, metadata: Optional[Dict] = None):
            self.document_id = document_id
            self.content = content
            self.mime_type = mime_type
            self.metadata = metadata or {}

from docling_converter import DoclingConverter
from formatters import HTMLFormatter, MarkdownFormatter


class EnhancedDocumentProcessor:
    """Enhanced document processor using Docling for better extraction and metadata preservation."""

    # Supported formats with their MIME types
    SUPPORTED_FORMATS = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.txt': 'text/plain',
        '.md': 'text/plain',
        '.html': 'text/html',
        '.htm': 'text/html',
        # Add more formats as Docling supports them
    }

    def __init__(self,
                 output_format: str = 'html',
                 preserve_images: bool = True,
                 preserve_tables: bool = True,
                 enable_ocr: bool = False):
        """
        Initialize the enhanced document processor.

        Args:
            output_format: 'html' or 'markdown' for the intermediate format
            preserve_images: Whether to extract and preserve images with bounding boxes
            preserve_tables: Whether to extract and preserve table structures
            enable_ocr: Whether to enable OCR for scanned documents
        """
        self.output_format = output_format.lower()
        if self.output_format not in ['html', 'markdown']:
            raise ValueError("output_format must be 'html' or 'markdown'")

        self.docling_converter = DoclingConverter(
            preserve_images=preserve_images,
            preserve_tables=preserve_tables,
            enable_ocr=enable_ocr
        )

        self.formatters = {
            'html': HTMLFormatter(),
            'markdown': MarkdownFormatter()
        }

    @staticmethod
    def _extract_text_from_file(file_path: str) -> str:
        """Fallback text extraction for unsupported formats."""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1 for binary files
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                return f"[Binary file - {os.path.basename(file_path)} - {os.path.getsize(file_path)} bytes]"
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return f"[Error reading file: {e}]"

    def create_rag_document_from_file(self,
                                    file_path: str,
                                    document_id: Optional[str] = None,
                                    **kwargs) -> Optional[RAGDocument]:
        """
        Create a RAGDocument from a file path using Docling for enhanced extraction.

        Args:
            file_path: Path to the document file
            document_id: Optional custom document ID
            **kwargs: Additional options passed to Docling converter

        Returns:
            RAGDocument with enhanced content and metadata, or None if processing fails
        """
        try:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return None

            if document_id is None:
                document_id = os.path.basename(file_path)

            file_ext = os.path.splitext(file_path)[1].lower()

            # Check if format is supported
            if file_ext not in self.SUPPORTED_FORMATS:
                print(f"Unsupported file type: {file_ext}")
                return None

            # Use Docling for supported formats
            try:
                conversion_result = self.docling_converter.convert_document(file_path, **kwargs)

                # Get formatted content
                formatter = self.formatters[self.output_format]
                formatted_content = formatter.format(conversion_result)
                print(f"DEBUG: formatted_content type = {type(formatted_content)}, len = {len(formatted_content) if hasattr(formatted_content, '__len__') else 'N/A'}")

                # Prepare metadata with enhanced information
                metadata = {
                    "file_path": file_path,
                    "file_type": file_ext,
                    "file_size": os.path.getsize(file_path),
                    "original_mime_type": self.SUPPORTED_FORMATS[file_ext],
                    "processing_method": "docling",
                    "output_format": self.output_format,
                    "docling_metadata": {
                        "page_count": len(conversion_result.document.pages),
                        "has_images": len([item for item, _ in conversion_result.document.iterate_items()
                                         if hasattr(item, 'label') and hasattr(item.label, '__str__') and 'picture' in str(item.label).lower()]) > 0,
                        "has_tables": len([item for item, _ in conversion_result.document.iterate_items()
                                         if hasattr(item, 'label') and hasattr(item.label, '__str__') and 'table' in str(item.label).lower()]) > 0,
                    }
                }

                # Determine MIME type for output
                mime_type = "text/html" if self.output_format == 'html' else "text/plain"

                rag_doc = RAGDocument(
                    document_id=document_id,
                    content=formatted_content,
                    mime_type=mime_type,
                    metadata=metadata
                )
                print(f"DEBUG: Created RAGDocument type = {type(rag_doc)}, id = {rag_doc['document_id'] if isinstance(rag_doc, dict) else rag_doc.document_id}")
                return rag_doc

            except Exception as e:
                print(f"Docling processing failed for {file_path}, falling back to basic extraction: {e}")
                # Fallback to basic extraction
                content = self._extract_text_from_file(file_path)
                return RAGDocument(
                    document_id=document_id,
                    content=content,
                    mime_type="text/plain",
                    metadata={
                        "file_path": file_path,
                        "file_type": file_ext,
                        "file_size": os.path.getsize(file_path),
                        "original_mime_type": self.SUPPORTED_FORMATS.get(file_ext, "text/plain"),
                        "processing_method": "fallback",
                        "error": str(e)
                    }
                )

        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return None

    @staticmethod
    def create_rag_document_from_text(text: str,
                                    document_id: str,
                                    metadata: Optional[Dict] = None) -> RAGDocument:
        """Create a RAGDocument from plain text (unchanged from original)."""
        if metadata is None:
            metadata = {}
        return RAGDocument(
            document_id=document_id,
            content=text,
            mime_type="text/plain",
            metadata=metadata
        )

    @staticmethod
    def create_rag_document_from_url(url: str,
                                   document_id: str,
                                   metadata: Optional[Dict] = None) -> RAGDocument:
        """Create a RAGDocument from a URL (unchanged from original)."""
        if metadata is None:
            metadata = {}
        return RAGDocument(
            document_id=document_id,
            content=url,
            mime_type="text/plain",
            metadata=metadata
        )

    def process_documents_directory(self,
                                  documents_dir: str,
                                  **kwargs) -> List[RAGDocument]:
        """Process all documents in a directory and return a list of RAGDocument objects."""
        rag_documents: List[RAGDocument] = []
        try:
            if not os.path.exists(documents_dir):
                print(f"Documents directory not found: {documents_dir}")
                return []

            for filename in os.listdir(documents_dir):
                file_path = os.path.join(documents_dir, filename)
                if os.path.isfile(file_path):
                    rag_doc = self.create_rag_document_from_file(
                        file_path=file_path,
                        document_id=f"doc-{filename}",
                        **kwargs
                    )
                    if rag_doc:
                        rag_documents.append(rag_doc)
                        print(f"Processed document: {filename}")
                    else:
                        print(f"Failed to process document: {filename}")
            print(f"Successfully processed {len(rag_documents)} documents")
            return rag_documents
        except Exception as e:
            print(f"Error processing documents directory: {e}")
            return []

    def create_chunks_for_vector_io(self,
                                  file_path: str,
                                  chunk_size: int = 1000,
                                  **kwargs) -> List[Dict]:
        """
        Create chunks for direct vector_io insertion with enhanced metadata.

        This method uses Docling to extract structured content and creates
        intelligent chunks that preserve document structure and metadata.
        """
        try:
            if not os.path.exists(file_path):
                return []

            file_ext = os.path.splitext(file_path)[1].lower()

            # Use Docling for supported formats
            if file_ext in self.SUPPORTED_FORMATS:
                try:
                    conversion_result = self.docling_converter.convert_document(file_path, **kwargs)
                    formatter = self.formatters[self.output_format]

                    # Create structured chunks with preserved metadata
                    chunks = formatter.create_chunks(conversion_result, chunk_size)

                    # Add file metadata to each chunk
                    for i, chunk in enumerate(chunks):
                        chunk['metadata'].update({
                            "document_id": os.path.basename(file_path),
                            "chunk_index": i,
                            "file_path": file_path,
                            "file_type": file_ext,
                            "processing_method": "docling_enhanced",
                            "output_format": self.output_format,
                        })

                    return chunks

                except Exception as e:
                    print(f"Docling chunking failed for {file_path}, falling back: {e}")

            # Fallback for unsupported formats
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            chunks = []
            for i in range(0, len(content), chunk_size):
                chunk_content = content[i:i + chunk_size]
                chunks.append({
                    "content": chunk_content,
                    "mime_type": "text/plain",
                    "metadata": {
                        "document_id": os.path.basename(file_path),
                        "chunk_index": len(chunks),
                        "file_path": file_path,
                        "file_type": file_ext,
                        "processing_method": "fallback",
                    },
                })
            return chunks

        except Exception as e:
            print(f"Error creating chunks for {file_path}: {e}")
            return []

    def get_document_structure(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed document structure information including elements and their positions.

        Returns:
            Dictionary containing document structure with bounding boxes and element types
        """
        try:
            conversion_result = self.docling_converter.convert_document(file_path)
            formatter = self.formatters[self.output_format]
            return formatter.get_document_structure(conversion_result)
        except Exception as e:
            print(f"Error getting document structure for {file_path}: {e}")
            return None
