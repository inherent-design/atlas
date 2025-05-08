"""
Unit tests for document chunking strategies.

These tests verify that various chunking strategies correctly split documents
into appropriate chunks based on content, structure, and size constraints.
"""

import unittest
from unittest import mock
import hashlib
import re

from atlas.knowledge.chunking import (
    DocumentChunk,
    ChunkingStrategy,
    FixedSizeChunker,
    SemanticChunker,
    MarkdownChunker,
    CodeChunker,
    ChunkingStrategyFactory,
    DuplicateContentDetector,
)
from atlas.tests.helpers.decorators import unit_test


class TestDocumentChunk(unittest.TestCase):
    """Test the DocumentChunk class."""
    
    @unit_test
    def test_document_chunk_initialization(self):
        """Test creating a DocumentChunk instance."""
        # Create a DocumentChunk
        chunk = DocumentChunk(
            id="test-doc#1",
            text="This is a test document chunk.",
            metadata={"source": "test.md"}
        )
        
        # Check basic properties
        self.assertEqual(chunk.id, "test-doc#1")
        self.assertEqual(chunk.text, "This is a test document chunk.")
        self.assertEqual(chunk.metadata, {"source": "test.md"})
        
        # Content hash should be automatically generated
        self.assertTrue(chunk.content_hash)
        self.assertEqual(len(chunk.content_hash), 64)  # SHA-256 hash is 64 hex chars
    
    @unit_test
    def test_document_chunk_with_custom_hash(self):
        """Test creating a DocumentChunk with a custom content hash."""
        custom_hash = "custom_hash_value"
        chunk = DocumentChunk(
            id="test-doc#1",
            text="This is a test document chunk.",
            metadata={"source": "test.md"},
            content_hash=custom_hash
        )
        
        # Hash should not be recalculated
        self.assertEqual(chunk.content_hash, custom_hash)
    
    @unit_test
    def test_content_normalization_for_hashing(self):
        """Test that content is normalized before hashing."""
        # Create two chunks with different formatting but same content
        chunk1 = DocumentChunk(
            id="test-doc#1",
            text="This is a test document.",
            metadata={"source": "test.md"}
        )
        
        chunk2 = DocumentChunk(
            id="test-doc#2",
            text="THIS  IS  A\nTEST\tDOCUMENT.",  # Different case, whitespace
            metadata={"source": "test.md"}
        )
        
        # Hashes should be the same after normalization
        self.assertEqual(chunk1.content_hash, chunk2.content_hash)
        
        # Different content should have different hashes
        chunk3 = DocumentChunk(
            id="test-doc#3",
            text="This is a different document.",
            metadata={"source": "test.md"}
        )
        
        self.assertNotEqual(chunk1.content_hash, chunk3.content_hash)
    
    @unit_test
    def test_normalization_function(self):
        """Test the text normalization function directly."""
        # Access the private method for testing
        normalize = DocumentChunk._normalize_for_hashing
        
        # Test various normalization scenarios
        self.assertEqual(normalize("Test"), "test")  # Lowercase
        self.assertEqual(normalize("  Test  "), "test")  # Trim whitespace
        self.assertEqual(normalize("Test\nString"), "test string")  # Newlines to space
        self.assertEqual(normalize("Test\t\tString"), "test string")  # Tabs to space
        self.assertEqual(normalize("Test   String"), "test string")  # Multiple spaces to one


class TestFixedSizeChunker(unittest.TestCase):
    """Test the FixedSizeChunker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)
        self.metadata = {"source": "test_document.md", "simple_id": "test_doc"}
    
    @unit_test
    def test_chunking_small_document(self):
        """Test chunking a document smaller than chunk size."""
        content = "This is a small document."
        chunks = self.chunker.chunk_document(content, self.metadata)
        
        # Should create a single chunk
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].text, content)
        self.assertEqual(chunks[0].id, "test_doc#0")
        self.assertEqual(chunks[0].metadata["chunk_index"], 0)
        self.assertEqual(chunks[0].metadata["chunk_size"], len(content))
    
    @unit_test
    def test_chunking_large_document(self):
        """Test chunking a document larger than chunk size."""
        # Create a document that spans multiple chunks
        content = "This is a test sentence. " * 10  # ~240 characters
        chunks = self.chunker.chunk_document(content, self.metadata)
        
        # Should create multiple overlapping chunks
        self.assertGreater(len(chunks), 1)
        
        # Check IDs are sequential
        for i, chunk in enumerate(chunks):
            self.assertEqual(chunk.id, f"test_doc#{i}")
            self.assertEqual(chunk.metadata["chunk_index"], i)
        
        # Verify overlap between chunks
        for i in range(len(chunks) - 1):
            end_of_first = chunks[i].text[-20:]
            start_of_second = chunks[i+1].text[:20]
            
            # Some text from the end of first chunk should appear at start of second
            self.assertTrue(
                end_of_first in chunks[i+1].text or start_of_second in chunks[i].text,
                f"No overlap between chunks {i} and {i+1}"
            )
    
    @unit_test
    def test_chunk_id_creation(self):
        """Test the creation of chunk IDs."""
        # Test with simple_id
        chunks = self.chunker.chunk_document("Test content", self.metadata)
        self.assertEqual(chunks[0].id, "test_doc#0")
        
        # Test with source but no simple_id
        metadata_no_simple_id = {"source": "test_document.md"}
        chunks = self.chunker.chunk_document("Test content", metadata_no_simple_id)
        self.assertEqual(chunks[0].id, "test_document.md#0")
        
        # Test with neither source nor simple_id
        metadata_no_ids = {"other_field": "value"}
        chunks = self.chunker.chunk_document("Test content", metadata_no_ids)
        self.assertEqual(chunks[0].id, "unknown#0")


class TestSemanticChunker(unittest.TestCase):
    """Test the SemanticChunker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.chunker = SemanticChunker(
            max_chunk_size=200,
            min_chunk_size=50,
            overlap_size=20
        )
        self.metadata = {"source": "test_document.md", "simple_id": "test_doc"}
    
    @unit_test
    def test_splitting_by_headings(self):
        """Test document splitting by headings."""
        content = """# Main Heading
This is an introduction paragraph.

## Section 1
This is content for section 1.

## Section 2
This is content for section 2.

### Subsection 2.1
This is content for subsection 2.1.
"""
        chunks = self.chunker.chunk_document(content, self.metadata)
        
        # Should create one chunk per section
        self.assertEqual(len(chunks), 4)
        
        # Check section titles in metadata
        self.assertEqual(chunks[0].metadata["section_title"], "Main Heading")
        self.assertEqual(chunks[1].metadata["section_title"], "Section 1")
        self.assertEqual(chunks[2].metadata["section_title"], "Section 2")
        self.assertEqual(chunks[3].metadata["section_title"], "Subsection 2.1")
        
        # Check content
        self.assertIn("# Main Heading", chunks[0].text)
        self.assertIn("## Section 1", chunks[1].text)
        self.assertIn("## Section 2", chunks[2].text)
        self.assertIn("### Subsection 2.1", chunks[3].text)
    
    @unit_test
    def test_splitting_document_without_headings(self):
        """Test document splitting when no headings are present."""
        content = "This is a document without any headings.\n\nIt has multiple paragraphs.\n\nBut no explicit section markers."
        chunks = self.chunker.chunk_document(content, self.metadata)
        
        # Should create a single chunk with a default title
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].metadata["section_title"], "This is a document without any headings.")
    
    @unit_test
    def test_splitting_large_section(self):
        """Test splitting a section that's too large."""
        # Create a heading followed by multiple paragraphs
        heading = "# Large Section\n\n"
        paragraphs = "This is paragraph 1.\n\n" * 15  # Should exceed max_chunk_size
        content = heading + paragraphs
        
        chunks = self.chunker.chunk_document(content, self.metadata)
        
        # Should split into multiple chunks
        self.assertGreater(len(chunks), 1)
        
        # All chunks should reference the same section
        for i, chunk in enumerate(chunks):
            self.assertIn("Large Section", chunk.metadata["section_title"])
            if i > 0:  # Parts after the first should be numbered
                self.assertIn("Part", chunk.metadata["section_title"])
            
            # Each chunk should include the heading
            self.assertIn("# Large Section", chunk.text)
    
    @unit_test
    def test_split_by_semantic_boundaries(self):
        """Test the _split_by_semantic_boundaries method directly."""
        content = """# Heading 1
Content 1

## Heading 2
Content 2

# Heading 3
Content 3"""
        
        sections = self.chunker._split_by_semantic_boundaries(content)
        
        # Should find 3 sections
        self.assertEqual(len(sections), 3)
        
        # Check section titles
        self.assertEqual(sections[0][0], "Heading 1")
        self.assertEqual(sections[1][0], "Heading 2")
        self.assertEqual(sections[2][0], "Heading 3")
        
        # Check section content
        self.assertIn("# Heading 1", sections[0][1])
        self.assertIn("Content 1", sections[0][1])
        self.assertIn("## Heading 2", sections[1][1])
        self.assertIn("Content 2", sections[1][1])
        self.assertIn("# Heading 3", sections[2][1])
        self.assertIn("Content 3", sections[2][1])


class TestMarkdownChunker(unittest.TestCase):
    """Test the MarkdownChunker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.chunker = MarkdownChunker(
            max_chunk_size=200,
            min_chunk_size=50,
            overlap_size=20
        )
        self.metadata = {"source": "test_document.md", "simple_id": "test_doc"}
    
    @unit_test
    def test_markdown_document_with_frontmatter(self):
        """Test chunking a markdown document with frontmatter."""
        content = """---
title: Test Document
author: Test Author
date: 2023-01-01
---

# Introduction
This is an introduction.

# Section 1
This is section 1 content.
"""
        chunks = self.chunker.chunk_document(content, self.metadata)
        
        # Should create chunks for the sections
        self.assertGreaterEqual(len(chunks), 2)
        
        # First chunk should include frontmatter
        self.assertIn("---", chunks[0].text)
        self.assertIn("title: Test Document", chunks[0].text)
        self.assertIn("# Introduction", chunks[0].text)
        
        # Second chunk should be section 1
        self.assertIn("# Section 1", chunks[1].text)
    
    @unit_test
    def test_extract_frontmatter(self):
        """Test the _extract_frontmatter method directly."""
        # Test with --- delimiters
        content = """---
title: Test
---

# Content
"""
        frontmatter, content_without_frontmatter = self.chunker._extract_frontmatter(content)
        self.assertIn("title: Test", frontmatter)
        self.assertEqual(content_without_frontmatter.strip(), "# Content")
        
        # Test with +++ delimiters
        content = """+++
title: Test
+++

# Content
"""
        frontmatter, content_without_frontmatter = self.chunker._extract_frontmatter(content)
        self.assertIn("title: Test", frontmatter)
        self.assertEqual(content_without_frontmatter.strip(), "# Content")
        
        # Test with no frontmatter
        content = "# Content"
        frontmatter, content_without_frontmatter = self.chunker._extract_frontmatter(content)
        self.assertEqual(frontmatter, "")
        self.assertEqual(content_without_frontmatter, "# Content")


class TestCodeChunker(unittest.TestCase):
    """Test the CodeChunker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.chunker = CodeChunker(
            max_chunk_size=500,
            min_chunk_size=100
        )
        self.metadata = {"source": "test_file.py", "simple_id": "test_file"}
    
    @unit_test
    def test_python_code_chunking(self):
        """Test chunking Python code."""
        content = """
# Test Python file
import sys
import os

class TestClass:
    \"\"\"A test class.\"\"\"
    
    def __init__(self, name):
        self.name = name
        
    def method1(self):
        \"\"\"First method.\"\"\"
        return f"Method 1 called by {self.name}"
        
    def method2(self):
        \"\"\"Second method.\"\"\"
        return f"Method 2 called by {self.name}"

def main():
    \"\"\"Main function.\"\"\"
    test = TestClass("Test")
    print(test.method1())
    print(test.method2())

if __name__ == "__main__":
    main()
"""
        chunks = self.chunker.chunk_document(content, self.metadata)
        
        # Should identify the imports, class, and main function
        self.assertGreaterEqual(len(chunks), 2)
        
        # Check for class and function chunks
        class_chunk = None
        main_chunk = None
        
        for chunk in chunks:
            if "class TestClass" in chunk.text:
                class_chunk = chunk
            elif "def main()" in chunk.text:
                main_chunk = chunk
        
        self.assertIsNotNone(class_chunk, "Class chunk not found")
        self.assertIsNotNone(main_chunk, "Main function chunk not found")
        
        self.assertEqual(class_chunk.metadata["definition_type"], "class")
        self.assertIn("method1", class_chunk.text)
        self.assertIn("method2", class_chunk.text)
        
        self.assertEqual(main_chunk.metadata["definition_type"], "function")
        self.assertIn("main()", main_chunk.text)
    
    @unit_test
    def test_javascript_code_chunking(self):
        """Test chunking JavaScript code."""
        content = """
// Test JavaScript file
import React from 'react';

class TestComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = { count: 0 };
  }
  
  incrementCount = () => {
    this.setState(prevState => ({ count: prevState.count + 1 }));
  }
  
  render() {
    return (
      <div>
        <p>Count: {this.state.count}</p>
        <button onClick={this.incrementCount}>Increment</button>
      </div>
    );
  }
}

const ArrowFunction = () => {
  return <div>Arrow Function Component</div>;
};

function NormalFunction() {
  return <div>Normal Function Component</div>;
}

export default TestComponent;
"""
        
        # Set JavaScript file extension in metadata
        js_metadata = {"source": "test_file.jsx", "simple_id": "test_file"}
        chunks = self.chunker.chunk_document(content, js_metadata)
        
        # Should identify the class and function components
        self.assertGreaterEqual(len(chunks), 3)
        
        # Check definitions were detected
        class_chunk = None
        arrow_chunk = None
        normal_chunk = None
        
        for chunk in chunks:
            if "class TestComponent" in chunk.text:
                class_chunk = chunk
            elif "const ArrowFunction" in chunk.text:
                arrow_chunk = chunk
            elif "function NormalFunction" in chunk.text:
                normal_chunk = chunk
        
        self.assertIsNotNone(class_chunk, "Class chunk not found")
        self.assertIsNotNone(arrow_chunk, "Arrow function chunk not found")
        self.assertIsNotNone(normal_chunk, "Normal function chunk not found")
    
    @unit_test
    def test_large_function_splitting(self):
        """Test that large functions are split into multiple chunks."""
        # Create a very large function that exceeds max_chunk_size
        function_def = "def large_function():\n    \"\"\"A very large function.\"\"\"\n"
        function_body = "    # Line of code\n" * 100  # Should exceed max_chunk_size
        content = function_def + function_body
        
        chunks = self.chunker.chunk_document(content, self.metadata)
        
        # Should split into multiple chunks
        self.assertGreater(len(chunks), 1)
        
        # All chunks should have the function definition
        for i, chunk in enumerate(chunks):
            if i > 0:  # Parts after the first should have continued marker
                self.assertIn("/* continued */", chunk.text)
            
            self.assertIn("def large_function", chunk.text)
            self.assertIn("part", chunk.metadata["definition_type"])
    
    @unit_test
    def test_generic_code_chunking(self):
        """Test generic code chunking for unknown file types."""
        # Create content without clear language-specific patterns
        content = """
This is some generic code or configuration.
It doesn't match any specific language pattern.
But it still needs to be chunked appropriately.

Line 1
Line 2
Line 3
...
Line 100
"""
        # Set generic file extension
        generic_metadata = {"source": "config.txt", "simple_id": "config"}
        
        # Make the content large enough to require splitting
        content = content + "\n".join([f"Line {i}" for i in range(1, 200)])
        
        chunks = self.chunker.chunk_document(content, generic_metadata)
        
        # Should use generic chunking and split by size
        self.assertGreater(len(chunks), 1)
        
        # Each chunk should have sequential index
        for i, chunk in enumerate(chunks):
            self.assertEqual(chunk.metadata["chunk_index"], i)


class TestChunkingStrategyFactory(unittest.TestCase):
    """Test the ChunkingStrategyFactory class."""
    
    @unit_test
    def test_create_strategy(self):
        """Test creating different chunking strategies."""
        # Test markdown strategy
        strategy = ChunkingStrategyFactory.create_strategy("markdown")
        self.assertIsInstance(strategy, MarkdownChunker)
        
        # Test code strategy
        strategy = ChunkingStrategyFactory.create_strategy("code")
        self.assertIsInstance(strategy, CodeChunker)
        
        # Test semantic strategy
        strategy = ChunkingStrategyFactory.create_strategy("semantic")
        self.assertIsInstance(strategy, SemanticChunker)
        
        # Test default (fixed size)
        strategy = ChunkingStrategyFactory.create_strategy("unknown")
        self.assertIsInstance(strategy, FixedSizeChunker)
    
    @unit_test
    def test_create_strategy_with_params(self):
        """Test creating strategies with custom parameters."""
        # Test with custom parameters
        strategy = ChunkingStrategyFactory.create_strategy(
            "markdown",
            max_chunk_size=300,
            min_chunk_size=100
        )
        self.assertIsInstance(strategy, MarkdownChunker)
        self.assertEqual(strategy.max_chunk_size, 300)
        self.assertEqual(strategy.min_chunk_size, 100)
    
    @unit_test
    def test_detect_document_type(self):
        """Test document type detection."""
        # Test by file extension
        self.assertEqual(ChunkingStrategyFactory.detect_document_type("document.md"), "markdown")
        self.assertEqual(ChunkingStrategyFactory.detect_document_type("script.py"), "code")
        self.assertEqual(ChunkingStrategyFactory.detect_document_type("file.txt"), "semantic")
        
        # Test by content
        markdown_content = "# Heading\n\nSome text with [a link](https://example.com)."
        self.assertEqual(
            ChunkingStrategyFactory.detect_document_type("file.txt", markdown_content),
            "markdown"
        )
        
        code_content = "import os\n\ndef main():\n    print('Hello')"
        self.assertEqual(
            ChunkingStrategyFactory.detect_document_type("file.txt", code_content),
            "code"
        )


class TestDuplicateContentDetector(unittest.TestCase):
    """Test the DuplicateContentDetector class."""
    
    @unit_test
    def test_duplicate_detection(self):
        """Test detecting duplicate content in chunks."""
        detector = DuplicateContentDetector()
        
        # Create chunks with some duplicates
        chunks = [
            DocumentChunk(id="doc1#1", text="This is chunk 1.", metadata={}),
            DocumentChunk(id="doc1#2", text="This is chunk 2.", metadata={}),
            DocumentChunk(id="doc2#1", text="This is chunk 1.", metadata={}),  # Duplicate of doc1#1
            DocumentChunk(id="doc2#2", text="This is unique content.", metadata={}),
        ]
        
        processed_chunks = detector.process_chunks(chunks)
        
        # All chunks should be returned, with duplicates marked
        self.assertEqual(len(processed_chunks), 4)
        
        # Check that the duplicate is marked
        self.assertNotIn("duplicate_of", processed_chunks[0].metadata)
        self.assertNotIn("duplicate_of", processed_chunks[1].metadata)
        self.assertEqual(processed_chunks[2].metadata["duplicate_of"], "doc1#1")
        self.assertNotIn("duplicate_of", processed_chunks[3].metadata)
        
        # Check unique chunk count
        self.assertEqual(detector.get_unique_chunk_count(), 3)
    
    @unit_test
    def test_reset_detector(self):
        """Test resetting the duplicate detector."""
        detector = DuplicateContentDetector()
        
        # Process some chunks
        chunks = [
            DocumentChunk(id="doc1#1", text="This is a test.", metadata={}),
            DocumentChunk(id="doc1#2", text="Another test.", metadata={}),
        ]
        
        detector.process_chunks(chunks)
        self.assertEqual(detector.get_unique_chunk_count(), 2)
        
        # Reset the detector
        detector.reset()
        self.assertEqual(detector.get_unique_chunk_count(), 0)
        
        # Process more chunks after reset
        more_chunks = [
            DocumentChunk(id="doc2#1", text="This is a test.", metadata={}),  # Would be duplicate before reset
        ]
        
        processed_chunks = detector.process_chunks(more_chunks)
        self.assertEqual(detector.get_unique_chunk_count(), 1)
        self.assertNotIn("duplicate_of", processed_chunks[0].metadata)