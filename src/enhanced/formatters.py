"""
Formatters for HTML and Markdown output with metadata preservation.

This module provides formatters that convert Docling conversion results
into HTML and Markdown formats while preserving bounding boxes and other metadata.
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

try:
    from docling.datamodel.document import *
    from docling_core.types.doc import GroupItem, ProvenanceItem, BoundingBox
    from docling_core.types.doc.document import DEFAULT_EXPORT_LABELS, GroupLabel
except ImportError:
    # Handle case where docling is not installed
    pass


class BaseFormatter(ABC):
    """Base class for document formatters."""

    @abstractmethod
    def format(self, conversion_result) -> str:
        """Format the conversion result into the target format."""
        pass

    @abstractmethod
    def create_chunks(self, conversion_result, chunk_size: int) -> List[Dict]:
        """Create chunks from the conversion result."""
        pass

    @abstractmethod
    def get_document_structure(self, conversion_result) -> Dict[str, Any]:
        """Get structured document information."""
        pass


class HTMLFormatter(BaseFormatter):
    """Formatter for HTML output with metadata preservation."""

    def format(self, conversion_result) -> str:
        """Convert Docling result to HTML with bounding boxes and metadata."""
        return self._export_to_html(conversion_result.document)

    def _export_to_html(self, document, labels=None, strict_text: bool = False) -> str:
        """Convert document to HTML format with enhanced metadata."""
        if labels is None:
            labels = DEFAULT_EXPORT_LABELS

        html_parts = []
        list_element = None

        for ix, (item, level) in enumerate(document.iterate_items(document.body, with_groups=True)):
            # Handle list groups
            if isinstance(item, GroupItem) and item.label in [GroupLabel.LIST, GroupLabel.ORDERED_LIST]:
                attrs = {"className": "list_wrapper"}
                if item.label == GroupLabel.LIST:
                    element = "ul"
                elif item.label == GroupLabel.ORDERED_LIST:
                    element = "ol"

                list_element = ET.Element(element, attrib=attrs)
                continue

            # Close list element if needed
            elif item.label not in [DocItemLabel.LIST_ITEM] and list_element is not None:
                html_list = ET.tostring(list_element, encoding='unicode', method='html')
                html_parts.append(html_list)
                list_element = None

            elif isinstance(item, GroupItem):
                continue

            # Get provenance information
            if hasattr(item, 'prov') and item.prov:
                prov = item.prov[0]
                attrs = self._prov_to_attr_dict(prov, document)
            else:
                attrs = {}

            # Handle different item types
            if isinstance(item, TextItem) and item.label in [DocItemLabel.TITLE]:
                html_parts.append(self._html_element("h1", "title_wrapper", attrs, item.text))

            elif isinstance(item, TextItem) and item.label in [DocItemLabel.SECTION_HEADER]:
                html_parts.append(self._html_element(f"h{level + 1}", "section_wrapper", attrs, item.text))

            elif isinstance(item, TextItem) and item.label in [DocItemLabel.PARAGRAPH]:
                html_parts.append(self._html_element("p", "paragraph_wrapper", attrs, item.text))

            elif isinstance(item, TextItem) and item.label in [DocItemLabel.CODE]:
                html_parts.append(self._html_element("code", "code_wrapper", attrs, item.text))

            elif isinstance(item, ListItem) and item.label in [DocItemLabel.LIST_ITEM]:
                attrs["className"] = "listitem_wrapper"
                attrs = {key: str(value) for key, value in attrs.items()}

                li = ET.SubElement(list_element, "li", attrib=attrs)
                li.text = item.text

            elif isinstance(item, TextItem) and item.label in labels:
                html_parts.append(self._html_element("div", "text_wrapper", attrs, item.text))

            elif isinstance(item, TableItem):
                table_html = self._convert_table_to_html(item, document)
                html_parts.append(self._html_element("div", "table_wrapper", attrs, table_html))

                # Add caption if present
                if not len(item.caption_text(document)) == 0:
                    html_parts.append(self._html_element("div", "caption_wrapper", {}, item.caption_text(document)))

            elif isinstance(item, PictureItem) and not strict_text:
                img_element = self._html_element("img", "", {"src": item.image.uri})
                html_parts.append(self._html_element("div", "image_wrapper", attrs, img_element))

                # Add caption if present
                if not len(item.caption_text(document)) == 0:
                    html_parts.append(self._html_element("div", "caption_wrapper", {}, item.caption_text(document)))
                    
            # TODO: add more item types here

        # Close any remaining list
        if list_element is not None:
            html_list = ET.tostring(list_element, encoding='unicode', method='html')
            html_parts.append(html_list)

        return "\n\n".join(html_parts)

    def _html_element(self, tag: str, class_name: str, attrs: Dict, content: Optional[str] = None) -> str:
        """Create HTML element with attributes."""
        attrs_str = ' '.join(f'{key}="{value}"' for key, value in attrs.items())

        if tag == "img":
            assert "src" in attrs.keys()
            return f'<{tag} className="{class_name}" {attrs_str}/>' if attrs_str else f'<{tag} className="{class_name}"/>'

        if content is not None:
            return f'<{tag} className="{class_name}" {attrs_str}>{content}</{tag}>' if attrs_str else f'<{tag} className="{class_name}">{content}</{tag}>'
        else:
            return f'<{tag} className="{class_name}" {attrs_str}/>' if attrs_str else f'<{tag} className="{class_name}"/>'

    def _prov_to_attr_dict(self, prov: ProvenanceItem, document) -> Dict[str, Any]:
        """Convert provenance to HTML attributes."""
        bbox = prov.bbox.to_top_left_origin(document.pages[prov.page_no].size.height)
        return {
            "bbox": list(bbox.as_tuple()),
            "page_index": prov.page_no - 1  # Convert to 0-based indexing
        }

    def _convert_table_to_html(self, item, document) -> str:
        """Convert Docling table to HTML with metadata."""
        # Simple table conversion - can be enhanced based on needs
        table_html = "<table>"
        if hasattr(item, 'data') and hasattr(item.data, 'table_cells'):
            # Group cells by row
            rows = {}
            for cell in item.data.table_cells:
                row_idx = cell.start_row_offset_idx
                if row_idx not in rows:
                    rows[row_idx] = []
                rows[row_idx].append(cell)

            # Create HTML rows
            for row_idx in sorted(rows.keys()):
                table_html += "<tr>"
                for cell in sorted(rows[row_idx], key=lambda c: c.start_col_offset_idx):
                    cell_attrs = f'colspan="{cell.end_col_offset_idx - cell.start_col_offset_idx}" ' \
                               f'rowspan="{cell.end_row_offset_idx - cell.start_row_offset_idx}"'
                    table_html += f"<td {cell_attrs}>{cell.text}</td>"
                table_html += "</tr>"

        table_html += "</table>"
        return table_html

    def create_chunks(self, conversion_result, chunk_size: int) -> List[Dict]:
        """Create chunks from HTML content with preserved structure."""
        html_content = self.format(conversion_result)

        # Split HTML by double newlines (paragraphs/elements)
        html_parts = html_content.split('\n\n')

        chunks = []
        current_chunk = []
        current_length = 0

        for part in html_parts:
            part_length = len(part)

            # If adding this part would exceed chunk size and we have content, create a chunk
            if current_length + part_length > chunk_size and current_chunk:
                chunk_content = '\n\n'.join(current_chunk)
                chunks.append({
                    "content": chunk_content,
                    "mime_type": "text/html",
                    "metadata": {
                        "chunk_type": "html_element_group",
                        "element_count": len(current_chunk),
                        "content_length": len(chunk_content),
                    }
                })
                current_chunk = []
                current_length = 0

            # If single part is larger than chunk size, split it
            if part_length > chunk_size:
                # For very large elements, create multiple chunks
                words = part.split()
                temp_chunk = []
                temp_length = 0

                for word in words:
                    if temp_length + len(word) + 1 > chunk_size and temp_chunk:
                        chunk_content = ' '.join(temp_chunk)
                        chunks.append({
                            "content": chunk_content,
                            "mime_type": "text/html",
                            "metadata": {
                                "chunk_type": "html_partial",
                                "is_partial": True,
                                "content_length": len(chunk_content),
                            }
                        })
                        temp_chunk = []
                        temp_length = 0

                    temp_chunk.append(word)
                    temp_length += len(word) + 1

                if temp_chunk:
                    chunk_content = ' '.join(temp_chunk)
                    current_chunk.append(chunk_content)
                    current_length += len(chunk_content)
            else:
                current_chunk.append(part)
                current_length += part_length + 2  # +2 for \n\n

        # Add remaining content
        if current_chunk:
            chunk_content = '\n\n'.join(current_chunk)
            chunks.append({
                "content": chunk_content,
                "mime_type": "text/html",
                "metadata": {
                    "chunk_type": "html_element_group",
                    "element_count": len(current_chunk),
                    "content_length": len(chunk_content),
                }
            })

        return chunks

    def get_document_structure(self, conversion_result) -> Dict[str, Any]:
        """Get document structure with HTML-specific information."""
        document = conversion_result.document
        structure = {
            'format': 'html',
            'pages': [],
            'elements': []
        }

        for page_idx, page in enumerate(document.pages):
            page_info = {
                'page_index': page_idx,
                'size': page.size,
                'elements': []
            }

            for item, level in document.iterate_items():
                if hasattr(item, 'prov') and item.prov:
                    for prov in item.prov:
                        if prov.page_no - 1 == page_idx:
                            element_info = {
                                'type': str(item.label) if hasattr(item, 'label') else 'unknown',
                                'level': level,
                                'bbox': list(prov.bbox.as_tuple()) if hasattr(prov, 'bbox') else None,
                                'html_tag': self._get_html_tag_for_item(item),
                                'text': item.text if hasattr(item, 'text') else None,
                            }
                            page_info['elements'].append(element_info)
                            break

            structure['pages'].append(page_info)
            structure['elements'].extend(page_info['elements'])

        return structure

    def _get_html_tag_for_item(self, item) -> str:
        """Get appropriate HTML tag for a document item."""
        if isinstance(item, TextItem):
            if item.label in [DocItemLabel.TITLE]:
                return 'h1'
            elif item.label in [DocItemLabel.SECTION_HEADER]:
                return 'h2'  # Simplified, could be h2-h6 based on level
            elif item.label in [DocItemLabel.PARAGRAPH]:
                return 'p'
            elif item.label in [DocItemLabel.CODE]:
                return 'code'
            else:
                return 'div'
        elif isinstance(item, TableItem):
            return 'table'
        elif isinstance(item, PictureItem):
            return 'img'
        elif isinstance(item, ListItem):
            return 'li'
        else:
            return 'div'


class MarkdownFormatter(BaseFormatter):
    """Formatter for Markdown output with metadata preservation."""

    def format(self, conversion_result) -> str:
        """Convert Docling result to Markdown with metadata comments."""
        return self._export_to_markdown(conversion_result.document)

    def _export_to_markdown(self, document, labels=None) -> str:
        """Convert document to Markdown format."""
        if labels is None:
            labels = DEFAULT_EXPORT_LABELS

        md_parts = []
        list_stack = []

        for ix, (item, level) in enumerate(document.iterate_items(document.body, with_groups=True)):
            # Handle list groups
            if isinstance(item, GroupItem) and item.label in [GroupLabel.LIST, GroupLabel.ORDERED_LIST]:
                list_stack.append(item.label)
                continue

            # Handle list items
            elif isinstance(item, ListItem) and item.label in [DocItemLabel.LIST_ITEM]:
                indent = "  " * (len(list_stack) - 1)
                marker = "- " if list_stack and list_stack[-1] == GroupLabel.LIST else f"{len(md_parts) + 1}. "
                md_parts.append(f"{indent}{marker}{item.text}")

                # Check if this is the last item in current list
                if len(list_stack) > 0:
                    list_stack.pop()

            # Handle other items
            elif isinstance(item, TextItem):
                if isinstance(item, GroupItem):
                    continue

                # Add metadata comment if provenance available
                if hasattr(item, 'prov') and item.prov:
                    prov = item.prov[0]
                    bbox = prov.bbox.as_tuple() if hasattr(prov, 'bbox') else None
                    md_parts.append(f"<!-- bbox: {bbox}, page: {prov.page_no - 1} -->")

                # Format based on item type
                if item.label in [DocItemLabel.TITLE]:
                    md_parts.append(f"# {item.text}")
                elif item.label in [DocItemLabel.SECTION_HEADER]:
                    md_parts.append(f"{'#' * (level + 1)} {item.text}")
                elif item.label in [DocItemLabel.PARAGRAPH]:
                    md_parts.append(item.text)
                elif item.label in [DocItemLabel.CODE]:
                    md_parts.append(f"```\n{item.text}\n```")
                else:
                    md_parts.append(item.text)

            elif isinstance(item, TableItem):
                table_md = self._convert_table_to_markdown(item, document)
                md_parts.append(table_md)

                # Add caption if present
                if not len(item.caption_text(document)) == 0:
                    md_parts.append(f"*{item.caption_text(document)}*")

            elif isinstance(item, PictureItem):
                # Add image with alt text
                alt_text = item.caption_text(document) if item.caption_text(document) else "Document image"
                md_parts.append(f"![{alt_text}]({item.image.uri})")

        return "\n\n".join(md_parts)

    def _convert_table_to_markdown(self, item, document) -> str:
        """Convert Docling table to Markdown table."""
        if not hasattr(item, 'data') or not hasattr(item.data, 'table_cells'):
            return ""

        # Group cells by row and column
        rows = {}
        max_col = 0

        for cell in item.data.table_cells:
            row_idx = cell.start_row_offset_idx
            col_idx = cell.start_col_offset_idx

            if row_idx not in rows:
                rows[row_idx] = {}
            rows[row_idx][col_idx] = cell.text or ""
            max_col = max(max_col, col_idx)

        # Convert to markdown table
        md_table = []
        sorted_rows = sorted(rows.keys())

        for row_idx in sorted_rows:
            row_data = []
            for col_idx in range(max_col + 1):
                cell_text = rows[row_idx].get(col_idx, "")
                row_data.append(cell_text)

            md_table.append(" | ".join(row_data))

            # Add separator after first row
            if row_idx == 0:
                md_table.append(" | ".join(["---"] * len(row_data)))

        return "\n".join(md_table)

    def create_chunks(self, conversion_result, chunk_size: int) -> List[Dict]:
        """Create chunks from Markdown content."""
        md_content = self.format(conversion_result)

        # Split by double newlines (paragraphs/sections)
        md_parts = md_content.split('\n\n')

        chunks = []
        current_chunk = []
        current_length = 0

        for part in md_parts:
            part_length = len(part)

            # If adding this part would exceed chunk size, create a chunk
            if current_length + part_length > chunk_size and current_chunk:
                chunk_content = '\n\n'.join(current_chunk)
                chunks.append({
                    "content": chunk_content,
                    "mime_type": "text/plain",
                    "metadata": {
                        "chunk_type": "markdown_section",
                        "element_count": len(current_chunk),
                        "content_length": len(chunk_content),
                    }
                })
                current_chunk = []
                current_length = 0

            # Handle very large parts
            if part_length > chunk_size:
                words = part.split()
                temp_chunk = []
                temp_length = 0

                for word in words:
                    if temp_length + len(word) + 1 > chunk_size and temp_chunk:
                        chunk_content = ' '.join(temp_chunk)
                        chunks.append({
                            "content": chunk_content,
                            "mime_type": "text/plain",
                            "metadata": {
                                "chunk_type": "markdown_partial",
                                "is_partial": True,
                                "content_length": len(chunk_content),
                            }
                        })
                        temp_chunk = []
                        temp_length = 0

                    temp_chunk.append(word)
                    temp_length += len(word) + 1

                if temp_chunk:
                    chunk_content = ' '.join(temp_chunk)
                    current_chunk.append(chunk_content)
                    current_length += len(chunk_content)
            else:
                current_chunk.append(part)
                current_length += part_length + 2

        # Add remaining content
        if current_chunk:
            chunk_content = '\n\n'.join(current_chunk)
            chunks.append({
                "content": chunk_content,
                "mime_type": "text/plain",
                "metadata": {
                    "chunk_type": "markdown_section",
                    "element_count": len(current_chunk),
                    "content_length": len(chunk_content),
                }
            })

        return chunks

    def get_document_structure(self, conversion_result) -> Dict[str, Any]:
        """Get document structure with Markdown-specific information."""
        document = conversion_result.document
        structure = {
            'format': 'markdown',
            'pages': [],
            'elements': []
        }

        for page_idx, page in enumerate(document.pages):
            page_info = {
                'page_index': page_idx,
                'size': page.size,
                'elements': []
            }

            for item, level in document.iterate_items():
                if hasattr(item, 'prov') and item.prov:
                    for prov in item.prov:
                        if prov.page_no - 1 == page_idx:
                            element_info = {
                                'type': str(item.label) if hasattr(item, 'label') else 'unknown',
                                'level': level,
                                'bbox': list(prov.bbox.as_tuple()) if hasattr(prov, 'bbox') else None,
                                'markdown_element': self._get_markdown_element_for_item(item),
                                'text': item.text if hasattr(item, 'text') else None,
                            }
                            page_info['elements'].append(element_info)
                            break

            structure['pages'].append(page_info)
            structure['elements'].extend(page_info['elements'])

        return structure

    def _get_markdown_element_for_item(self, item) -> str:
        """Get appropriate Markdown element type for a document item."""
        if isinstance(item, TextItem):
            if item.label in [DocItemLabel.TITLE]:
                return 'heading_1'
            elif item.label in [DocItemLabel.SECTION_HEADER]:
                return f'heading_{min(6, 2)}'  # Simplified
            elif item.label in [DocItemLabel.PARAGRAPH]:
                return 'paragraph'
            elif item.label in [DocItemLabel.CODE]:
                return 'code_block'
            else:
                return 'text'
        elif isinstance(item, TableItem):
            return 'table'
        elif isinstance(item, PictureItem):
            return 'image'
        elif isinstance(item, ListItem):
            return 'list_item'
        else:
            return 'unknown'
