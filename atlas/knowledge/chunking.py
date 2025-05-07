"""
Chunking strategies for Atlas knowledge ingestion.

This module contains interfaces and implementations for different document chunking
strategies, including adaptive chunking with semantic boundaries and content deduplication.

IMPORTANT: This module is designed to be imported by other modules in the knowledge package.
It should NOT import from other Atlas modules to avoid circular dependencies.
"""

import re
import logging
import hashlib
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """A single chunk of a document."""
    id: str
    text: str
    metadata: Dict[str, Any]
    content_hash: str = ""

    def __post_init__(self):
        """Generate a content hash if not already set."""
        if not self.content_hash:
            # Create a normalized representation for hashing
            normalized_text = self._normalize_for_hashing(self.text)
            self.content_hash = hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()

    @staticmethod
    def _normalize_for_hashing(text: str) -> str:
        """Normalize text for more robust content hashing.
        
        Removes excess whitespace, converts to lowercase, and other normalizations
        to ensure semantically identical content produces the same hash.
        """
        # Convert to lowercase
        text = text.lower()
        
        # Replace multiple spaces, newlines, tabs with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text


class ChunkingStrategy(ABC):
    """Base class for document chunking strategies."""
    
    @abstractmethod
    def chunk_document(self, content: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Split a document into chunks according to the strategy.
        
        Args:
            content: The document content to chunk.
            metadata: Metadata about the document.
            
        Returns:
            A list of DocumentChunk objects.
        """
        pass
    
    def _create_chunk_id(self, metadata: Dict[str, Any], chunk_index: int) -> str:
        """Create a unique ID for a chunk.
        
        Args:
            metadata: The document metadata.
            chunk_index: The index of the chunk within the document.
            
        Returns:
            A unique chunk ID using simplified format if available.
        """
        # Use simplified ID if available, otherwise fall back to source
        id_base = metadata.get("simple_id", metadata.get("source", "unknown"))
        return f"{id_base}#{chunk_index}"


class FixedSizeChunker(ChunkingStrategy):
    """Simple chunking strategy that splits documents into fixed-size chunks."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize the fixed size chunker.
        
        Args:
            chunk_size: The target size of each chunk in characters.
            chunk_overlap: The overlap between chunks in characters.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_document(self, content: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Split a document into fixed-size chunks with overlap.
        
        Args:
            content: The document content to chunk.
            metadata: Metadata about the document.
            
        Returns:
            A list of DocumentChunk objects.
        """
        chunks = []
        
        # For very small documents, don't split
        if len(content) <= self.chunk_size:
            chunk_id = self._create_chunk_id(metadata, 0)
            chunks.append(DocumentChunk(
                id=chunk_id,
                text=content,
                metadata={**metadata, "chunk_index": 0, "chunk_size": len(content)}
            ))
            return chunks
        
        # For larger documents, split with overlap
        start = 0
        chunk_index = 0
        
        while start < len(content):
            # Calculate end position with overlap
            end = min(start + self.chunk_size, len(content))
            
            # Extract chunk text
            chunk_text = content[start:end]
            
            # Create chunk
            chunk_id = self._create_chunk_id(metadata, chunk_index)
            chunks.append(DocumentChunk(
                id=chunk_id,
                text=chunk_text,
                metadata={
                    **metadata, 
                    "chunk_index": chunk_index,
                    "chunk_size": len(chunk_text)
                }
            ))
            
            # Move to next chunk start position (with overlap)
            start = end - self.chunk_overlap if end < len(content) else len(content)
            chunk_index += 1
        
        return chunks


class SemanticChunker(ChunkingStrategy):
    """Chunking strategy that respects semantic boundaries like paragraphs and sections."""
    
    def __init__(
        self, 
        max_chunk_size: int = 2000,
        min_chunk_size: int = 200,
        overlap_size: int = 100,
    ):
        """Initialize the semantic chunker.
        
        Args:
            max_chunk_size: Maximum size of a chunk in characters.
            min_chunk_size: Minimum size of a chunk in characters.
            overlap_size: Size of overlap to add between chunks.
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap_size = overlap_size
    
    def chunk_document(self, content: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Split a document into chunks respecting semantic boundaries.
        
        Args:
            content: The document content to chunk.
            metadata: Metadata about the document.
            
        Returns:
            A list of DocumentChunk objects.
        """
        # First, identify semantic boundaries in the document
        sections = self._split_by_semantic_boundaries(content)
        
        # Process each section into appropriate chunks
        chunks = []
        chunk_index = 0
        
        for section_title, section_content in sections:
            # For small sections, keep them as a single chunk
            if len(section_content) <= self.max_chunk_size:
                chunk_id = self._create_chunk_id(metadata, chunk_index)
                chunks.append(DocumentChunk(
                    id=chunk_id,
                    text=section_content,
                    metadata={
                        **metadata, 
                        "chunk_index": chunk_index,
                        "section_title": section_title,
                        "chunk_size": len(section_content)
                    }
                ))
                chunk_index += 1
                continue
            
            # For larger sections, split into smaller chunks respecting paragraph boundaries
            section_chunks = self._split_section_by_paragraphs(section_content, section_title)
            
            for i, chunk_text in enumerate(section_chunks):
                chunk_id = self._create_chunk_id(metadata, chunk_index)
                chunks.append(DocumentChunk(
                    id=chunk_id,
                    text=chunk_text,
                    metadata={
                        **metadata, 
                        "chunk_index": chunk_index,
                        "section_title": f"{section_title} (Part {i+1}/{len(section_chunks)})",
                        "chunk_size": len(chunk_text)
                    }
                ))
                chunk_index += 1
                
        return chunks
    
    def _split_by_semantic_boundaries(self, content: str) -> List[Tuple[str, str]]:
        """Split document content by headings and other semantic boundaries.
        
        Args:
            content: The document content to split.
            
        Returns:
            A list of (section_title, section_content) tuples.
        """
        # Match headings with the following pattern: one or more #'s followed by text
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        
        # Find all headings
        headings = list(heading_pattern.finditer(content))
        
        sections = []
        
        # If no headings, treat the entire document as one section
        if not headings:
            # Try to extract a title from metadata or first line
            first_line = content.strip().split('\n', 1)[0] if content.strip() else "Document"
            if len(first_line) > 50:  # Too long to be a sensible title
                first_line = "Document"
                
            sections.append((first_line, content))
            return sections
            
        # Process each section defined by headings
        for i, match in enumerate(headings):
            heading_level = len(match.group(1))  # Number of # characters
            title = match.group(2).strip()
            start_pos = match.start()
            
            # Determine end position (start of next heading or end of document)
            if i < len(headings) - 1:
                end_pos = headings[i + 1].start()
            else:
                end_pos = len(content)
                
            # Get section text including the heading
            section_text = content[start_pos:end_pos].strip()
            
            sections.append((title, section_text))
            
        return sections
    
    def _split_section_by_paragraphs(self, section: str, section_title: str) -> List[str]:
        """Split a section into chunks respecting paragraph boundaries.
        
        Args:
            section: The section content to split.
            section_title: The title of the section.
            
        Returns:
            A list of chunk texts.
        """
        # Find paragraph boundaries (double newlines)
        paragraphs = re.split(r'\n\s*\n', section)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        # Always include the section title/heading in each chunk for context
        heading_match = re.match(r'^(#{1,6}\s+.+)$', section.split('\n', 1)[0], re.MULTILINE)
        section_heading = heading_match.group(1) if heading_match else f"# {section_title}"
        
        # Process paragraphs into chunks
        for paragraph in paragraphs:
            # If adding this paragraph would exceed max size and we already have content,
            # finish the current chunk and start a new one
            if current_size + len(paragraph) > self.max_chunk_size and current_size >= self.min_chunk_size:
                chunks.append('\n\n'.join(current_chunk))
                
                # Start new chunk with section heading for context
                current_chunk = [section_heading]
                current_size = len(section_heading)
                
                # If this paragraph contains the section heading, skip it as we already added it
                if paragraph.startswith(section_heading):
                    continue
            
            # Add paragraph to current chunk
            current_chunk.append(paragraph)
            current_size += len(paragraph) + 2  # +2 for the newlines
            
        # Add the last chunk if there's anything left
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            
        return chunks


class MarkdownChunker(SemanticChunker):
    """Specialized chunker for Markdown documents that respects markdown structure."""
    
    def __init__(
        self, 
        max_chunk_size: int = 2000,
        min_chunk_size: int = 200,
        overlap_size: int = 100,
    ):
        """Initialize the markdown chunker.
        
        Args:
            max_chunk_size: Maximum size of a chunk in characters.
            min_chunk_size: Minimum size of a chunk in characters.
            overlap_size: Size of overlap to add between chunks.
        """
        super().__init__(max_chunk_size, min_chunk_size, overlap_size)
        
    def chunk_document(self, content: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Split a markdown document into chunks respecting markdown structure.
        
        Args:
            content: The document content to chunk.
            metadata: Metadata about the document.
            
        Returns:
            A list of DocumentChunk objects.
        """
        # Preserve frontmatter if present
        frontmatter, content_without_frontmatter = self._extract_frontmatter(content)
        
        # Get chunks using the semantic chunker
        chunks = super().chunk_document(content_without_frontmatter, metadata)
        
        # Add frontmatter to the first chunk if present
        if frontmatter and chunks:
            chunks[0].text = frontmatter + "\n\n" + chunks[0].text
            
        return chunks
    
    def _extract_frontmatter(self, content: str) -> Tuple[str, str]:
        """Extract frontmatter from markdown content if present.
        
        Args:
            content: The markdown content.
            
        Returns:
            Tuple of (frontmatter, content_without_frontmatter)
        """
        # Look for frontmatter between --- or +++ delimiters
        frontmatter_pattern = re.compile(r'^---\s*$\n(.*?)\n^---\s*$\n', re.MULTILINE | re.DOTALL)
        match = frontmatter_pattern.match(content)
        
        if not match:
            # Try +++ delimiter
            frontmatter_pattern = re.compile(r'^\+\+\+\s*$\n(.*?)\n^\+\+\+\s*$\n', re.MULTILINE | re.DOTALL)
            match = frontmatter_pattern.match(content)
            
        if match:
            frontmatter = match.group(0)
            content_without_frontmatter = content[len(frontmatter):]
            return frontmatter, content_without_frontmatter
        else:
            return "", content


class CodeChunker(ChunkingStrategy):
    """Specialized chunker for code files that respects code structure."""
    
    def __init__(
        self, 
        max_chunk_size: int = 2500,
        min_chunk_size: int = 200,
    ):
        """Initialize the code chunker.
        
        Args:
            max_chunk_size: Maximum size of a chunk in characters.
            min_chunk_size: Minimum size of a chunk in characters.
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
    
    def chunk_document(self, content: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Split a code file into chunks respecting code structure.
        
        Args:
            content: The code content to chunk.
            metadata: Metadata about the document.
            
        Returns:
            A list of DocumentChunk objects.
        """
        # Extract file extension from metadata
        file_path = metadata.get("source", "")
        file_extension = file_path.split(".")[-1].lower() if "." in file_path else ""
        
        # Use language-specific chunking if available
        if file_extension in ["py", "python"]:
            return self._chunk_python(content, metadata)
        elif file_extension in ["js", "jsx", "ts", "tsx"]:
            return self._chunk_javascript(content, metadata)
        elif file_extension in ["java", "kt", "scala"]:
            return self._chunk_java_like(content, metadata)
        elif file_extension in ["c", "cpp", "h", "hpp", "cc"]:
            return self._chunk_c_like(content, metadata)
        else:
            # Fall back to generic code chunking
            return self._chunk_generic_code(content, metadata)
    
    def _chunk_python(self, content: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Split Python code into semantic chunks.
        
        Args:
            content: The Python code.
            metadata: Metadata about the document.
            
        Returns:
            A list of DocumentChunk objects.
        """
        # Match Python class and function definitions
        class_pattern = re.compile(r"^class\s+\w+(?:\(.*?\))?:", re.MULTILINE)
        function_pattern = re.compile(r"^def\s+\w+\s*\(.*?\):", re.MULTILINE)
        
        # Find all class and function definitions
        classes = list(class_pattern.finditer(content))
        functions = list(function_pattern.finditer(content))
        
        # Combine and sort by position
        definitions = sorted(classes + functions, key=lambda x: x.start())
        
        return self._create_chunks_from_definitions(content, definitions, metadata)
    
    def _chunk_javascript(self, content: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Split JavaScript/TypeScript code into semantic chunks.
        
        Args:
            content: The JavaScript code.
            metadata: Metadata about the document.
            
        Returns:
            A list of DocumentChunk objects.
        """
        # Match JavaScript class and function definitions
        class_pattern = re.compile(r"^class\s+\w+(?:\s+extends\s+\w+)?(?:\s+implements\s+\w+(?:,\s*\w+)*)?(?:\s*\{)", re.MULTILINE)
        function_pattern = re.compile(r"^(?:async\s+)?function\s*\*?\s*\w*\s*\(.*?\)\s*(?:=>\s*)?(?:\{|$)", re.MULTILINE)
        arrow_function_pattern = re.compile(r"^(?:export\s+)?(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\(.*?\)\s*=>\s*(?:\{|$)", re.MULTILINE)
        
        # Find all definitions
        classes = list(class_pattern.finditer(content))
        functions = list(function_pattern.finditer(content))
        arrow_functions = list(arrow_function_pattern.finditer(content))
        
        # Combine and sort by position
        definitions = sorted(classes + functions + arrow_functions, key=lambda x: x.start())
        
        return self._create_chunks_from_definitions(content, definitions, metadata)
    
    def _chunk_java_like(self, content: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Split Java-like code into semantic chunks.
        
        Args:
            content: The Java-like code.
            metadata: Metadata about the document.
            
        Returns:
            A list of DocumentChunk objects.
        """
        # Match Java-like class and method definitions
        class_pattern = re.compile(r"^(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+\w+(?:\s+extends\s+\w+)?(?:\s+implements\s+\w+(?:,\s*\w+)*)?(?:\s*\{)", re.MULTILINE)
        method_pattern = re.compile(r"^(?:public|private|protected)?\s*(?:static|final|abstract)?\s*[\w<>]+\s+\w+\s*\(.*?\)\s*(?:throws\s+[\w,\s]+)?\s*(?:\{|$)", re.MULTILINE)
        
        # Find all definitions
        classes = list(class_pattern.finditer(content))
        methods = list(method_pattern.finditer(content))
        
        # Combine and sort by position
        definitions = sorted(classes + methods, key=lambda x: x.start())
        
        return self._create_chunks_from_definitions(content, definitions, metadata)
    
    def _chunk_c_like(self, content: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Split C-like code into semantic chunks.
        
        Args:
            content: The C-like code.
            metadata: Metadata about the document.
            
        Returns:
            A list of DocumentChunk objects.
        """
        # Match C-like function definitions
        function_pattern = re.compile(r"^[\w\*]+\s+\w+\s*\(.*?\)\s*(?:\{|$)", re.MULTILINE)
        struct_pattern = re.compile(r"^(?:typedef\s+)?struct\s+\w*\s*\{", re.MULTILINE)
        
        # Find all definitions
        functions = list(function_pattern.finditer(content))
        structs = list(struct_pattern.finditer(content))
        
        # Combine and sort by position
        definitions = sorted(functions + structs, key=lambda x: x.start())
        
        return self._create_chunks_from_definitions(content, definitions, metadata)
    
    def _chunk_generic_code(self, content: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Split generic code into chunks using line breaks and size limits.
        
        Args:
            content: The code content.
            metadata: Metadata about the document.
            
        Returns:
            A list of DocumentChunk objects.
        """
        # Split by empty lines
        lines = content.split('\n')
        
        chunks = []
        current_chunk_lines = []
        current_size = 0
        chunk_index = 0
        
        for line in lines:
            line_size = len(line) + 1  # +1 for the newline
            
            # If adding this line would exceed max size and we already have content,
            # finish the current chunk and start a new one
            if current_size + line_size > self.max_chunk_size and current_size >= self.min_chunk_size:
                chunk_text = '\n'.join(current_chunk_lines)
                chunk_id = self._create_chunk_id(metadata, chunk_index)
                
                chunks.append(DocumentChunk(
                    id=chunk_id,
                    text=chunk_text,
                    metadata={
                        **metadata, 
                        "chunk_index": chunk_index,
                        "chunk_size": len(chunk_text)
                    }
                ))
                
                current_chunk_lines = []
                current_size = 0
                chunk_index += 1
            
            # Add line to current chunk
            current_chunk_lines.append(line)
            current_size += line_size
        
        # Add the last chunk if there's anything left
        if current_chunk_lines:
            chunk_text = '\n'.join(current_chunk_lines)
            chunk_id = self._create_chunk_id(metadata, chunk_index)
            
            chunks.append(DocumentChunk(
                id=chunk_id,
                text=chunk_text,
                metadata={
                    **metadata, 
                    "chunk_index": chunk_index,
                    "chunk_size": len(chunk_text)
                }
            ))
        
        return chunks
    
    def _create_chunks_from_definitions(
        self, 
        content: str, 
        definitions: List[re.Match],
        metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """Create chunks from code based on definitions.
        
        Args:
            content: The code content.
            definitions: List of regex matches for code definitions.
            metadata: Metadata about the document.
            
        Returns:
            A list of DocumentChunk objects.
        """
        chunks = []
        chunk_index = 0
        
        # If no definitions found, use generic chunking
        if not definitions:
            return self._chunk_generic_code(content, metadata)
        
        # Handle content before first definition
        if definitions and definitions[0].start() > 0:
            preamble = content[:definitions[0].start()]
            if len(preamble.strip()) > 0:
                chunk_id = self._create_chunk_id(metadata, chunk_index)
                chunks.append(DocumentChunk(
                    id=chunk_id,
                    text=preamble,
                    metadata={
                        **metadata, 
                        "chunk_index": chunk_index,
                        "definition_type": "preamble",
                        "chunk_size": len(preamble)
                    }
                ))
                chunk_index += 1
        
        # Process each definition
        for i, definition in enumerate(definitions):
            # Determine end position (start of next definition or end of content)
            start_pos = definition.start()
            if i < len(definitions) - 1:
                end_pos = definitions[i + 1].start()
            else:
                end_pos = len(content)
                
            # Extract definition text
            definition_text = content[start_pos:end_pos]
            
            # Extract definition type and name
            def_line = definition.group(0)
            def_type = "class" if "class" in def_line else "function"
            
            # If chunk is too large, split it further
            if len(definition_text) > self.max_chunk_size:
                subcontent = definition_text
                lines = subcontent.split('\n')
                
                current_lines = []
                current_size = 0
                subcontent_index = 0
                
                # Always include definition line
                definition_line = lines[0]
                current_lines.append(definition_line)
                current_size = len(definition_line) + 1
                
                for line in lines[1:]:
                    line_size = len(line) + 1
                    
                    if current_size + line_size > self.max_chunk_size and current_size >= self.min_chunk_size:
                        # Finish current chunk
                        chunk_text = '\n'.join(current_lines)
                        chunk_id = self._create_chunk_id(metadata, chunk_index)
                        
                        chunks.append(DocumentChunk(
                            id=chunk_id,
                            text=chunk_text,
                            metadata={
                                **metadata, 
                                "chunk_index": chunk_index,
                                "definition_type": f"{def_type} (part {subcontent_index+1})",
                                "definition_line": def_line,
                                "chunk_size": len(chunk_text)
                            }
                        ))
                        
                        # Start new chunk with definition line again for context
                        current_lines = [definition_line + " /* continued */"]
                        current_size = len(definition_line) + 15  # +15 for "/* continued */"
                        chunk_index += 1
                        subcontent_index += 1
                    
                    # Add line to current chunk
                    current_lines.append(line)
                    current_size += line_size
                
                # Add last chunk if needed
                if current_lines:
                    chunk_text = '\n'.join(current_lines)
                    chunk_id = self._create_chunk_id(metadata, chunk_index)
                    
                    chunks.append(DocumentChunk(
                        id=chunk_id,
                        text=chunk_text,
                        metadata={
                            **metadata, 
                            "chunk_index": chunk_index,
                            "definition_type": f"{def_type} (part {subcontent_index+1})",
                            "definition_line": def_line,
                            "chunk_size": len(chunk_text)
                        }
                    ))
                    chunk_index += 1
            else:
                # Add as single chunk
                chunk_id = self._create_chunk_id(metadata, chunk_index)
                chunks.append(DocumentChunk(
                    id=chunk_id,
                    text=definition_text,
                    metadata={
                        **metadata, 
                        "chunk_index": chunk_index,
                        "definition_type": def_type,
                        "definition_line": def_line,
                        "chunk_size": len(definition_text)
                    }
                ))
                chunk_index += 1
        
        return chunks


class ChunkingStrategyFactory:
    """Factory for creating chunking strategies based on document type."""
    
    @staticmethod
    def create_strategy(document_type: str, **kwargs) -> ChunkingStrategy:
        """Create a chunking strategy appropriate for the document type.
        
        Args:
            document_type: The type of document to chunk.
            **kwargs: Additional parameters for the chunker.
            
        Returns:
            A ChunkingStrategy instance.
        """
        if document_type == "markdown":
            return MarkdownChunker(**kwargs)
        elif document_type == "code":
            return CodeChunker(**kwargs)
        elif document_type == "semantic":
            return SemanticChunker(**kwargs)
        else:
            # Default to fixed size chunker
            return FixedSizeChunker(**kwargs)
    
    @staticmethod
    def detect_document_type(file_path: str, content: Optional[str] = None) -> str:
        """Detect the document type based on file extension and/or content.
        
        Args:
            file_path: Path to the document.
            content: Optional document content for more accurate detection.
            
        Returns:
            The detected document type.
        """
        # First check file extension
        if file_path.endswith((".md", ".markdown", ".mdown")):
            return "markdown"
        elif file_path.endswith((".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".go", ".rb", ".php", ".cs")):
            return "code"
        
        # If content is provided, try to detect based on content
        if content:
            # Check for markdown formatting
            if re.search(r'^#{1,6}\s+.+$|^\*\*\*.+$|\[.+\]\(.+\)', content, re.MULTILINE):
                return "markdown"
            
            # Check for code patterns
            if re.search(r'^(class|def|function|import|from|package|using|#include)\b', content, re.MULTILINE):
                return "code"
        
        # Default to semantic chunking for unknown types
        return "semantic"


class DuplicateContentDetector:
    """Detect and manage duplicate content across document chunks."""
    
    def __init__(self):
        """Initialize the duplicate content detector."""
        self.content_hashes = {}  # Map from content hash to document ID
    
    def process_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Process chunks to detect and mark duplicates.
        
        Args:
            chunks: List of document chunks to process.
            
        Returns:
            List of chunks with duplicates marked or removed.
        """
        unique_chunks = []
        
        for chunk in chunks:
            if chunk.content_hash in self.content_hashes:
                # This is a duplicate - add reference to the original in metadata
                original_id = self.content_hashes[chunk.content_hash]
                logger.info(f"Detected duplicate content: chunk {chunk.id} duplicates {original_id}")
                
                # We could either skip this chunk or add with duplicate reference
                # Here we choose to add it with a reference
                chunk.metadata["duplicate_of"] = original_id
                unique_chunks.append(chunk)
            else:
                # This is a new chunk
                self.content_hashes[chunk.content_hash] = chunk.id
                unique_chunks.append(chunk)
        
        return unique_chunks
    
    def get_unique_chunk_count(self) -> int:
        """Get the count of unique chunks seen so far.
        
        Returns:
            The number of unique chunks.
        """
        return len(self.content_hashes)
    
    def reset(self) -> None:
        """Reset the duplicate detector state."""
        self.content_hashes = {}