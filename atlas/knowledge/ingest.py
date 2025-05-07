"""
Document ingestion for the Atlas framework.

This module handles processing documents into a format suitable for vector storage and retrieval,
with support for adaptive chunking, deduplication, and real-time directory monitoring.
"""

import os
import re
import glob
import sys
import time
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Union, Set
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

import chromadb
import pathspec
from anthropic import Anthropic

from atlas.core import env
from atlas.knowledge.embedding import EmbeddingStrategy, EmbeddingStrategyFactory

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


@dataclass
class FileMetadata:
    """Metadata about a document file."""
    source: str  # Relative path to the file
    file_name: str  # Name of the file
    file_type: str  # Type/extension of the file
    created_at: str  # File creation timestamp
    last_modified: str  # File modification timestamp
    version: str = "current"  # Document version
    size_bytes: int = 0  # File size in bytes
    simple_id: str = ""  # Simplified ID format (parent_dir/filename)


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
    
    def _split_by_semantic_boundaries(self, content: str) -> List[tuple[str, str]]:
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
    
    def _extract_frontmatter(self, content: str) -> tuple[str, str]:
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


class DocumentProcessor:
    """Document processor with adaptive chunking and deduplication.
    
    This enhanced processor provides support for:
    - Adaptive document chunking based on document type
    - Content deduplication
    - Real-time directory monitoring
    """
    
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
        db_path: Optional[str] = None,
        enable_deduplication: bool = True,
        embedding_strategy: Optional[Union[str, EmbeddingStrategy]] = None,
    ):
        """Initialize the document processor.
        
        Args:
            anthropic_api_key: Optional API key for Anthropic.
            collection_name: Name of the Chroma collection to use.
            db_path: Optional path for ChromaDB storage.
            enable_deduplication: Whether to enable content deduplication.
            embedding_strategy: Strategy to use for embeddings.
        """
        self.anthropic_client = Anthropic(
            api_key=anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        
        # Get collection name from parameters, environment, or default
        self.collection_name = collection_name or env.get_string(
            "ATLAS_COLLECTION_NAME", "atlas_knowledge_base"
        )
        
        # Create an absolute path for ChromaDB storage (use provided or environment variable or default)
        self.db_path: str = ""
        if db_path:
            self.db_path = db_path
        else:
            env_db_path = env.get_string("ATLAS_DB_PATH")
            if env_db_path:
                self.db_path = env_db_path
                # Create directory if it doesn't exist
                db_path_obj = Path(self.db_path)
                db_path_obj.mkdir(exist_ok=True, parents=True)
            else:
                home_dir = Path.home()
                db_path_obj = home_dir / "atlas_chroma_db"
                db_path_obj.mkdir(exist_ok=True)
                self.db_path = str(db_path_obj.absolute())

        logger.info(f"ChromaDB persistence directory: {self.db_path}")
        print(f"ChromaDB persistence directory: {self.db_path}")
        
        # Initialize ChromaDB
        self._initialize_chroma_db()
        
        # Initialize embedding strategy
        if isinstance(embedding_strategy, EmbeddingStrategy):
            self.embedding_strategy = embedding_strategy
        elif isinstance(embedding_strategy, str):
            self.embedding_strategy = EmbeddingStrategyFactory.create_strategy(embedding_strategy)
        else:
            self.embedding_strategy = EmbeddingStrategyFactory.create_strategy("default")
        
        # Initialize deduplication if enabled
        self.enable_deduplication = enable_deduplication
        self.duplicate_detector = DuplicateContentDetector() if enable_deduplication else None
        
        # Load gitignore patterns
        self.gitignore_spec = self._load_gitignore()
        
        # Track processed files to avoid reprocessing
        self.processed_files: Dict[str, str] = {}  # file_path -> hash
        
        # Initialize directory watchers
        self.watchers: Dict[str, Observer] = {}  # directory -> Observer
    
    def _initialize_chroma_db(self) -> None:
        """Initialize the ChromaDB client and collection."""
        try:
            # List contents of DB directory
            if os.path.exists(self.db_path):
                print("Current contents of DB directory:")
                for item in os.listdir(self.db_path):
                    item_path = os.path.join(self.db_path, item)
                    if os.path.isdir(item_path):
                        print(f"  - {item}/ (directory)")
                    else:
                        size = os.path.getsize(item_path) / 1024  # Size in KB
                        print(f"  - {item} ({size:.2f} KB)")
            
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(path=self.db_path)
            print(f"ChromaDB client initialized successfully with persistence at: {self.db_path}")
            
            # List collections
            all_collections = self.chroma_client.list_collections()
            print(f"Available collections: {[c.name for c in all_collections]}")
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name
            )
            print(f"Collection '{self.collection_name}' accessed successfully")
            
            # Get initial document count
            self.initial_doc_count = self.collection.count()
            print(f"Collection initially contains {self.initial_doc_count} documents")
            
            if self.initial_doc_count == 0:
                print("NOTE: Collection is empty. Documents will be ingested from scratch.")
            
        except Exception as e:
            error_msg = f"Error initializing ChromaDB: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            
            # Fallback to in-memory if persistence fails
            print("Falling back to in-memory ChromaDB")
            self.chroma_client = chromadb.Client()
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name
            )
            self.initial_doc_count = 0
    
    def _load_gitignore(self) -> pathspec.PathSpec:
        """Load the gitignore patterns from the repository.
        
        Returns:
            A PathSpec object with the gitignore patterns.
        """
        gitignore_patterns = []
        
        # Default ignore patterns
        default_patterns = [
            "node_modules/",
            ".git/",
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".env",
            "venv/",
            "env/",
            ".DS_Store",
            ".vscode/",
            ".idea/",
            "*.so",
            "*.dylib",
            "*.dll",
            "dist/",
            "build/",
            "*.egg-info/",
        ]
        
        # Add default patterns
        gitignore_patterns.extend(default_patterns)
        
        # Look for .gitignore files
        gitignore_path = os.path.join(os.getcwd(), ".gitignore")
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if line and not line.startswith("#"):
                            gitignore_patterns.append(line)
                print(f"Loaded {len(gitignore_patterns) - len(default_patterns)} patterns from .gitignore")
            except Exception as e:
                print(f"Error loading .gitignore: {str(e)}")
        
        # Create PathSpec with gitignore patterns
        return pathspec.PathSpec.from_lines("gitwildmatch", gitignore_patterns)
    
    def is_ignored(self, path: str) -> bool:
        """Check if a path should be ignored based on gitignore patterns.
        
        Args:
            path: The path to check.
            
        Returns:
            True if the path should be ignored, False otherwise.
        """
        # Convert to relative path
        rel_path = os.path.relpath(path, os.getcwd())
        # Explicitly cast to bool to avoid Any return type
        return bool(self.gitignore_spec.match_file(rel_path))
    
    def get_all_markdown_files(self, base_dir: str) -> List[str]:
        """Get all markdown files in the specified directory and its subdirectories.
        
        Args:
            base_dir: The base directory to search from.
            
        Returns:
            A list of paths to markdown files.
        """
        all_md_files = glob.glob(f"{base_dir}/**/*.md", recursive=True)
        
        # Filter out ignored files
        filtered_files = [f for f in all_md_files if not self.is_ignored(f)]
        
        if len(all_md_files) != len(filtered_files):
            print(f"Excluded {len(all_md_files) - len(filtered_files)} files due to gitignore patterns")
        
        return filtered_files
    
    def get_file_hash(self, file_path: str) -> str:
        """Generate a hash of the file contents.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Hash of the file contents.
        """
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error generating hash for {file_path}: {e}")
            return ""
    
    def has_file_changed(self, file_path: str) -> bool:
        """Check if a file has changed since last processing.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            True if the file has changed, False otherwise.
        """
        current_hash = self.get_file_hash(file_path)
        previous_hash = self.processed_files.get(file_path)
        
        if not current_hash:
            return False  # Error reading file
        
        if not previous_hash:
            # File not processed before
            self.processed_files[file_path] = current_hash
            return True
        
        if current_hash != previous_hash:
            # File has changed
            self.processed_files[file_path] = current_hash
            return True
        
        return False  # File unchanged
    
    def create_file_metadata(self, file_path: str) -> FileMetadata:
        """Create metadata for a document file.
        
        Args:
            file_path: Path to the document.
            
        Returns:
            File metadata with simplified ID format.
        """
        file_stat = os.stat(file_path)
        rel_path = os.path.relpath(file_path, start=os.getcwd())
        file_name = os.path.basename(file_path)
        file_type = os.path.splitext(file_name)[1].lower()[1:]  # Remove leading dot
        
        # Extract version from path if available
        version_match = re.search(r"/v(\d+(?:\.\d+)?)/", file_path)
        version = version_match.group(1) if version_match else "current"
        
        # Format timestamps
        created_at = datetime.fromtimestamp(file_stat.st_ctime).isoformat()
        last_modified = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
        
        # Create simplified ID (parent_dir/filename format)
        path_parts = Path(rel_path).parts
        if len(path_parts) > 1:
            # Use parent directory and filename
            simple_id = f"{path_parts[-2]}/{file_name}"
        else:
            # Just use filename if no parent directory
            simple_id = file_name
        
        return FileMetadata(
            source=rel_path,
            file_name=file_name,
            file_type=file_type,
            created_at=created_at,
            last_modified=last_modified,
            version=version,
            size_bytes=file_stat.st_size,
            simple_id=simple_id,
        )
    
    def process_file(self, file_path: str) -> List[DocumentChunk]:
        """Process a file into chunks.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            A list of document chunks.
        """
        # Skip processing if file is ignored
        if self.is_ignored(file_path):
            logger.info(f"Skipping ignored file: {file_path}")
            return []
        
        # Check if file has changed
        if not self.has_file_changed(file_path):
            logger.info(f"Skipping unchanged file: {file_path}")
            return []
        
        # Log processing but don't print to avoid interfering with progress bar
        logger.info(f"Processing file: {file_path}")
        
        # Check file size and warn if it's very large
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 10:
            logger.warning(f"Processing large file ({file_size_mb:.1f} MB): {file_path}")
        
        # Read file content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return []
        
        # Create document metadata
        metadata = self.create_file_metadata(file_path)
        
        # Detect document type and create appropriate chunking strategy
        document_type = ChunkingStrategyFactory.detect_document_type(file_path, content)
        chunking_strategy = ChunkingStrategyFactory.create_strategy(document_type)
        
        # Create chunks
        chunks = chunking_strategy.chunk_document(
            content, 
            vars(metadata)  # Convert dataclass to dict
        )
        
        # Process for duplicates if enabled
        if self.enable_deduplication and self.duplicate_detector:
            chunks = self.duplicate_detector.process_chunks(chunks)
        
        return chunks
    
    def generate_embeddings(self, chunks: List[DocumentChunk]) -> None:
        """Generate embeddings for document chunks and store them in ChromaDB.
        
        Args:
            chunks: List of document chunks to embed.
        """
        if not chunks:
            return
        
        # Prepare data for Chroma
        chunk_count = len(chunks)
        ids = [chunk.id for chunk in chunks]
        texts = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        print(f"\nEmbedding Generation:")
        print("=" * 50)
        print(f"Total chunks to embed: {chunk_count}")
        
        # Calculate batch sizes for embedding
        estimated_token_count = sum(len(text.split()) * 1.3 for text in texts)  # Rough estimate
        estimated_embedding_time = estimated_token_count / 15000  # Rough estimate of tokens per second
        
        print(f"Estimated tokens: ~{int(estimated_token_count):,}")
        print(f"Estimated time: ~{estimated_embedding_time:.1f} seconds")
        print("-" * 50)
        
        # Progress tracking variables
        import threading
        import time
        import sys
        from datetime import datetime
        
        start_time = time.time()
        progress_active = True
        
        # Define a progress reporter thread
        def show_progress():
            step = 0
            phases = ["Preparing", "Embedding", "Storing in database"]
            phase_index = 0
            
            # Spinner animation characters
            spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            
            while progress_active:
                # Update spinner and phase
                spinner_char = spinner[step % len(spinner)]
                current_phase = phases[min(phase_index, len(phases)-1)]
                elapsed = time.time() - start_time
                
                # Progress message with elapsed time
                msg = f"\r{spinner_char} {current_phase} {chunk_count} chunks... "
                msg += f"[{elapsed:.1f}s elapsed]"
                
                # Add estimates
                if phase_index == 0 and elapsed > 2.0:
                    phase_index = 1  # Move to embedding phase after 2 seconds
                elif phase_index == 1 and elapsed > estimated_embedding_time * 0.7:
                    phase_index = 2  # Move to storing phase
                
                # Pad with spaces to overwrite previous line
                msg += " " * 50
                
                sys.stdout.write(msg)
                sys.stdout.flush()
                
                # Increment spinner step
                step += 1
                time.sleep(0.1)
        
        # Start progress thread
        progress_thread = threading.Thread(target=show_progress)
        progress_thread.daemon = True
        progress_thread.start()
        
        try:
            # Phase 1: Start embedding process
            embedding_start = time.time()
            
            # Phase 2: Get embeddings from the strategy
            embeddings = self.embedding_strategy.embed_documents(texts)
            embedding_end = time.time()
            embedding_duration = embedding_end - embedding_start
            
            # Phase 3: Store in database
            db_start = time.time()
            
            # Add data to Chroma collection
            if embeddings:
                self.collection.add(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas,
                    embeddings=embeddings
                )
            else:
                self.collection.add(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas
                )
            
            db_end = time.time()
            db_duration = db_end - db_start
            total_duration = time.time() - start_time
            
            # Stop progress reporting
            progress_active = False
            progress_thread.join(timeout=1.0)
            
            # Clear progress line
            sys.stdout.write("\r" + " " * 100 + "\r")
            sys.stdout.flush()
            
            # Log completion
            logger.info(f"Added {chunk_count} document chunks to Chroma DB")
            
            # Show performance stats
            print(f"✓ Embedding completed in {embedding_duration:.2f}s")
            print(f"✓ Database storage completed in {db_duration:.2f}s")
            print(f"✓ Total processing time: {total_duration:.2f}s")
            print(f"✓ Throughput: {chunk_count/total_duration:.1f} chunks/second")
            print(f"✓ Added {chunk_count} document chunks to Chroma DB")
            print("=" * 50)
            
        except Exception as e:
            # Stop progress reporting
            progress_active = False
            progress_thread.join(timeout=1.0)
            
            # Clear progress line
            sys.stdout.write("\r" + " " * 100 + "\r")
            sys.stdout.flush()
            
            # Log error
            logger.error(f"Error adding documents to ChromaDB: {e}")
            print(f"✗ Error: {str(e)}")
            print(f"✗ Failed to add documents to ChromaDB after {time.time() - start_time:.2f}s")
    
    def process_directory(self, directory: str, recursive: bool = True) -> int:
        """Process all files in a directory and its subdirectories.
        
        Args:
            directory: The directory to process.
            recursive: Whether to process subdirectories.
            
        Returns:
            Number of documents added.
        """
        # Find all markdown files in the directory
        files = self.get_all_markdown_files(directory) if recursive else glob.glob(f"{directory}/*.md")
        total_files = len(files)
        logger.info(f"Found {total_files} markdown files to process in {directory}")
        print(f"Found {total_files} markdown files to process in {directory}")
        
        if total_files == 0:
            print("No files to process.")
            return 0
            
        # Process each file with progress indicator
        all_chunks = []
        print("\nProcessing files:")
        print("="*50)
        progress_bar_width = 40
        
        for i, file_path in enumerate(files):
            # Calculate and display progress
            progress = (i / total_files)
            bar_length = int(progress * progress_bar_width)
            percent = int(progress * 100)
            
            # Create progress bar
            progress_bar = f"[{'#' * bar_length}{' ' * (progress_bar_width - bar_length)}] {percent}% "
            
            # Show file being processed
            file_name = os.path.basename(file_path)
            status_text = f"{progress_bar} Processing: {file_name} ({i+1}/{total_files})"
            # Pad with spaces to overwrite any leftover text from previous lines
            padding = ' ' * 50  # Add enough spaces to clear previous line
            print(f"{status_text}{padding}", end='\r')
            
            # Process the file
            chunks = self.process_file(file_path)
            all_chunks.extend(chunks)
        
        # Complete the progress bar with proper padding
        padding = ' ' * 100  # More padding to ensure line is clear
        print(f"[{'#' * progress_bar_width}] 100% Complete!{padding}")
        print("="*50)
        
        # Generate embeddings for all chunks
        if all_chunks:
            print("\nStarting embedding process...")
            self.generate_embeddings(all_chunks)
        else:
            print("\nNo new content to process.")
        
        # Report stats
        try:
            final_doc_count = self.collection.count()
            new_docs = final_doc_count - self.initial_doc_count
            
            print("\nFinal Processing Summary:")
            print("=" * 50)
            logger.info(f"Successfully processed {total_files} files into {len(all_chunks)} chunks")
            logger.info(f"Added {new_docs} new documents to collection (now contains {final_doc_count} total)")
            print(f"✓ Files processed:       {total_files}")
            print(f"✓ Chunks created:        {len(all_chunks)}")
            print(f"✓ New documents added:   {new_docs}")
            print(f"✓ Collection total size: {final_doc_count} documents")
            
            if self.enable_deduplication and self.duplicate_detector:
                dupes_found = len(all_chunks) - self.duplicate_detector.get_unique_chunk_count()
                if dupes_found > 0:
                    logger.info(f"Detected {dupes_found} duplicate chunks")
                    print(f"✓ Duplicates detected:   {dupes_found}")
            print("=" * 50)
            
            return new_docs
        except Exception as e:
            logger.error(f"Error getting final collection stats: {e}")
            print(f"\nError getting final collection stats: {e}")
            return 0
    
    def delete_directory_documents(self, directory: str) -> int:
        """Delete all documents from a directory from the collection.
        
        Args:
            directory: The directory to delete documents from.
            
        Returns:
            Number of documents deleted.
        """
        # Normalize directory path
        directory = os.path.normpath(directory)
        rel_directory = os.path.relpath(directory, start=os.getcwd())
        
        # Find all documents from this directory
        try:
            # First count documents to determine if we need to proceed
            all_documents = self.collection.get()
            count_before = len(all_documents["ids"])
            
            # Filter documents by directory
            documents_to_delete = []
            for i, metadata in enumerate(all_documents["metadatas"]):
                if "source" in metadata and metadata["source"].startswith(rel_directory):
                    documents_to_delete.append(all_documents["ids"][i])
            
            if documents_to_delete:
                logger.info(f"Deleting {len(documents_to_delete)} documents from {rel_directory}")
                print(f"Deleting {len(documents_to_delete)} documents from {rel_directory}")
                
                # Delete in batches to avoid any potential limitations
                batch_size = 1000
                for i in range(0, len(documents_to_delete), batch_size):
                    batch = documents_to_delete[i:i+batch_size]
                    self.collection.delete(ids=batch)
                
                # Count documents after deletion
                count_after = self.collection.count()
                deleted_count = count_before - count_after
                
                logger.info(f"Deleted {deleted_count} documents. Collection now contains {count_after} documents.")
                print(f"Deleted {deleted_count} documents. Collection now contains {count_after} documents.")
                return deleted_count
            
            logger.info(f"No documents found from directory {rel_directory}")
            return 0
        
        except Exception as e:
            logger.error(f"Error deleting documents from {rel_directory}: {e}")
            print(f"Error deleting documents from {rel_directory}: {e}")
            return 0
    
    def watch_directory(
        self, 
        directory: str, 
        recursive: bool = True,
        callback: Optional[Callable[[str], None]] = None
    ) -> None:
        """Set up a file watcher for a directory to enable real-time updates.
        
        Args:
            directory: The directory to watch.
            recursive: Whether to watch subdirectories.
            callback: Optional callback function to call when changes are detected.
        """
        if directory in self.watchers:
            logger.warning(f"Already watching directory: {directory}")
            return
        
        # Create a file event handler
        class FileChangeHandler(FileSystemEventHandler):
            def __init__(self, processor: DocumentProcessor, callback: Optional[Callable]):
                self.processor = processor
                self.callback = callback
                # Track recent events to avoid duplicate processing
                self.recent_events: Dict[str, float] = {}
                # Set a cooldown period (in seconds)
                self.cooldown = 2.0
            
            def on_any_event(self, event: FileSystemEvent) -> None:
                if event.is_directory:
                    return
                
                # Only process markdown files
                if not event.src_path.endswith((".md", ".markdown", ".mdown")):
                    return
                
                # Check if file is ignored
                if self.processor.is_ignored(event.src_path):
                    return
                
                # Check for cooldown to avoid processing the same file multiple times
                current_time = time.time()
                if event.src_path in self.recent_events:
                    last_time = self.recent_events[event.src_path]
                    if current_time - last_time < self.cooldown:
                        return
                
                # Update recent events
                self.recent_events[event.src_path] = current_time
                
                # Process the file
                logger.info(f"File change detected: {event.src_path}, event={event.event_type}")
                if event.event_type in ["created", "modified"]:
                    # Process the file
                    chunks = self.processor.process_file(event.src_path)
                    if chunks:
                        self.processor.generate_embeddings(chunks)
                        logger.info(f"Updated {len(chunks)} chunks for {event.src_path}")
                elif event.event_type == "deleted":
                    # Remove the file from tracked files
                    if event.src_path in self.processor.processed_files:
                        del self.processor.processed_files[event.src_path]
                    
                    # Note: We don't delete from Chroma here as we might want to keep historical data
                    logger.info(f"File deleted: {event.src_path}")
                
                # Call callback if provided
                if self.callback:
                    self.callback(event.src_path)
        
        # Create and start the observer
        event_handler = FileChangeHandler(self, callback)
        observer = Observer()
        observer.schedule(event_handler, directory, recursive=recursive)
        observer.start()
        
        # Store the observer
        self.watchers[directory] = observer
        
        logger.info(f"Started watching directory: {directory}")
        print(f"Started watching directory: {directory}")
    
    def stop_watching(self, directory: Optional[str] = None) -> None:
        """Stop watching a directory or all directories.
        
        Args:
            directory: The directory to stop watching, or None to stop all watchers.
        """
        if directory:
            # Stop watching a specific directory
            if directory in self.watchers:
                observer = self.watchers[directory]
                observer.stop()
                observer.join()
                del self.watchers[directory]
                logger.info(f"Stopped watching directory: {directory}")
                print(f"Stopped watching directory: {directory}")
            else:
                logger.warning(f"Not watching directory: {directory}")
        else:
            # Stop watching all directories
            for dir_path, observer in self.watchers.items():
                observer.stop()
                observer.join()
                logger.info(f"Stopped watching directory: {dir_path}")
            self.watchers.clear()
            print(f"Stopped watching all directories")
    
    def get_watcher_status(self) -> Dict[str, bool]:
        """Get the status of all directory watchers.
        
        Returns:
            A dictionary mapping directory paths to watcher status (True if active).
        """
        return {dir_path: observer.is_alive() for dir_path, observer in self.watchers.items()}
    
    def __del__(self) -> None:
        """Clean up resources when the processor is destroyed."""
        self.stop_watching()


def live_ingest_directory(
    directory: str,
    collection_name: Optional[str] = None,
    db_path: Optional[str] = None,
    recursive: bool = True,
    enable_deduplication: bool = True,
) -> DocumentProcessor:
    """Set up live ingestion for a directory.
    
    Args:
        directory: The directory to watch for changes.
        collection_name: Optional name for the ChromaDB collection.
        db_path: Optional path for ChromaDB storage.
        recursive: Whether to watch subdirectories.
        enable_deduplication: Whether to enable content deduplication.
        
    Returns:
        The document processor instance.
    """
    processor = DocumentProcessor(
        collection_name=collection_name,
        db_path=db_path,
        enable_deduplication=enable_deduplication,
    )
    
    # Process existing files first
    processor.process_directory(directory, recursive=recursive)
    
    # Set up watcher for future changes
    processor.watch_directory(directory, recursive=recursive)
    
    return processor


def main():
    """Main function to ingest Atlas documentation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced document ingestion for Atlas")
    parser.add_argument(
        "-d", "--directory", 
        help="Directory to process", 
        default="./docs"
    )
    parser.add_argument(
        "-c", "--collection", 
        help="Collection name", 
        default="atlas_knowledge_base"
    )
    parser.add_argument(
        "--db_path", 
        help="Path to ChromaDB storage", 
        default=None
    )
    parser.add_argument(
        "--no_dedup", 
        help="Disable content deduplication", 
        action="store_true"
    )
    parser.add_argument(
        "--watch", 
        help="Watch directory for changes", 
        action="store_true"
    )
    parser.add_argument(
        "--embedding", 
        help="Embedding strategy to use (default, anthropic, hybrid)", 
        default="default"
    )
    
    args = parser.parse_args()
    
    if args.watch:
        # Set up live ingestion
        processor = live_ingest_directory(
            directory=args.directory,
            collection_name=args.collection,
            db_path=args.db_path,
            enable_deduplication=not args.no_dedup,
        )
        
        # Keep process running
        try:
            print("Press Ctrl+C to stop watching...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping watchers...")
            processor.stop_watching()
            print("Done")
    else:
        # One-time processing
        processor = DocumentProcessor(
            collection_name=args.collection,
            db_path=args.db_path,
            enable_deduplication=not args.no_dedup,
            embedding_strategy=args.embedding,
        )
        processor.process_directory(args.directory)


if __name__ == "__main__":
    main()