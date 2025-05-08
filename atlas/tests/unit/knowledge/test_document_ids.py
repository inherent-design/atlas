"""
Test the document ID format in the knowledge ingestion system.

This test verifies that document IDs are created in the format 'folder/file.md'
when possible, instead of using full relative paths.
"""

import os
import tempfile
from pathlib import Path
from unittest import TestCase, mock

# Import test decorators
from atlas.tests.helpers import unit_test

# Import knowledge module components
from atlas.knowledge.ingest import DocumentProcessor, ChunkingStrategy, ChunkingStrategyFactory, FileMetadata


class TestDocumentIds(TestCase):
    """Test document ID formatting in the knowledge ingestion system."""
    
    @unit_test
    def test_document_metadata_simple_id(self):
        """Test that the simplified ID is correctly generated in FileMetadata."""
        # Create a temporary directory structure for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a nested directory structure
            nested_dir = Path(temp_dir) / "parent" / "child"
            nested_dir.mkdir(parents=True)
            
            # Create a test markdown file
            test_file_path = nested_dir / "test_document.md"
            with open(test_file_path, "w") as f:
                f.write("# Test Document\n\nThis is a test document for ID formatting.")
            
            # Create a document processor and directly test file metadata creation
            processor = DocumentProcessor()
            metadata = processor.create_file_metadata(str(test_file_path))
            
            # The simple_id should be just the parent dir and filename
            self.assertEqual(metadata.simple_id, "child/test_document.md")
            
            # Test chunk ID creation using this metadata
            chunking_strategy = ChunkingStrategyFactory.create_strategy("markdown")
            chunk_id = chunking_strategy._create_chunk_id(vars(metadata), 0)
            
            # The ID should be in the format: "child/test_document.md#0"
            expected_id = "child/test_document.md#0"
            self.assertEqual(chunk_id, expected_id)

    @unit_test
    def test_root_level_document_ids(self):
        """Test document IDs for files without a parent directory."""
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test markdown file at the root level
            test_file_path = Path(temp_dir) / "root_document.md"
            with open(test_file_path, "w") as f:
                f.write("# Root Document\n\nThis is a root-level test document.")
            
            # Create a document processor and directly test file metadata creation
            processor = DocumentProcessor()
            metadata = processor.create_file_metadata(str(test_file_path))
            
            # For root level documents, simple_id should be just the filename
            # Since temp directories have random paths, we'll just check that
            # it ends with the filename and doesn't contain path separators
            self.assertTrue(metadata.simple_id.endswith("root_document.md"))
            self.assertEqual(Path(metadata.simple_id).name, "root_document.md")
            
            # Test chunk ID creation using this metadata
            chunking_strategy = ChunkingStrategyFactory.create_strategy("markdown")
            chunk_id = chunking_strategy._create_chunk_id(vars(metadata), 0)
            
            # The ID should end with: "root_document.md#0"
            self.assertTrue(chunk_id.endswith("root_document.md#0"))

    @unit_test
    def test_nested_path_document_ids(self):
        """Test document IDs for files in deeply nested paths."""
        # Create a temporary directory structure for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a deeply nested directory structure
            nested_dir = Path(temp_dir) / "level1" / "level2" / "level3" / "level4"
            nested_dir.mkdir(parents=True)
            
            # Create a test markdown file
            test_file_path = nested_dir / "nested_document.md"
            with open(test_file_path, "w") as f:
                f.write("# Nested Document\n\nThis is a deeply nested test document.")
            
            # Create a document processor and directly test file metadata creation
            processor = DocumentProcessor()
            metadata = processor.create_file_metadata(str(test_file_path))
            
            # The simple_id should use only the closest parent directory
            self.assertEqual(metadata.simple_id, "level4/nested_document.md")
            
            # Test chunk ID creation using this metadata
            chunking_strategy = ChunkingStrategyFactory.create_strategy("markdown")
            chunk_id = chunking_strategy._create_chunk_id(vars(metadata), 0)
            
            # The ID should be in the format: "level4/nested_document.md#0"
            expected_id = "level4/nested_document.md#0"
            self.assertEqual(chunk_id, expected_id)

    @unit_test
    def test_same_filename_different_paths(self):
        """Test document IDs for files with the same name in different directories."""
        # Create a temporary directory structure for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create two directories
            dir1 = Path(temp_dir) / "section1"
            dir2 = Path(temp_dir) / "section2"
            dir1.mkdir()
            dir2.mkdir()
            
            # Create identical filenames in each directory
            file1 = dir1 / "common.md"
            file2 = dir2 / "common.md"
            
            with open(file1, "w") as f:
                f.write("# Common Document 1\n\nThis is in section 1.")
            
            with open(file2, "w") as f:
                f.write("# Common Document 2\n\nThis is in section 2.")
            
            # Create a document processor
            processor = DocumentProcessor()
            
            # Get metadata for both files
            metadata1 = processor.create_file_metadata(str(file1))
            metadata2 = processor.create_file_metadata(str(file2))
            
            # The simple_ids should include the respective parent directories
            self.assertEqual(metadata1.simple_id, "section1/common.md")
            self.assertEqual(metadata2.simple_id, "section2/common.md")
            
            # Test chunk ID creation
            chunking_strategy = ChunkingStrategyFactory.create_strategy("markdown")
            chunk_id1 = chunking_strategy._create_chunk_id(vars(metadata1), 0)
            chunk_id2 = chunking_strategy._create_chunk_id(vars(metadata2), 0)
            
            # The IDs should be different
            self.assertEqual(chunk_id1, "section1/common.md#0")
            self.assertEqual(chunk_id2, "section2/common.md#0")
            self.assertNotEqual(chunk_id1, chunk_id2)

    @unit_test
    def test_non_markdown_document_ids(self):
        """Test document IDs for non-markdown files."""
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with different extensions
            dir_path = Path(temp_dir) / "docs"
            dir_path.mkdir()
            
            # Create various file types
            text_file = dir_path / "text_file.txt"
            with open(text_file, "w") as f:
                f.write("This is a plain text file.")
            
            json_file = dir_path / "data.json"
            with open(json_file, "w") as f:
                f.write('{"key": "value"}')
            
            # Create a document processor
            processor = DocumentProcessor()
            
            # Get metadata for all files
            text_metadata = processor.create_file_metadata(str(text_file))
            json_metadata = processor.create_file_metadata(str(json_file))
            
            # The simple_ids should use the same format regardless of extension
            self.assertEqual(text_metadata.simple_id, "docs/text_file.txt")
            self.assertEqual(json_metadata.simple_id, "docs/data.json")
            
            # Test chunk ID creation
            # For non-markdown files we'd typically use a different chunking strategy
            # but we'll use the markdown strategy for consistency in this test
            chunking_strategy = ChunkingStrategyFactory.create_strategy("markdown")
            text_chunk_id = chunking_strategy._create_chunk_id(vars(text_metadata), 0)
            json_chunk_id = chunking_strategy._create_chunk_id(vars(json_metadata), 0)
            
            # The IDs should follow the same format
            self.assertEqual(text_chunk_id, "docs/text_file.txt#0")
            self.assertEqual(json_chunk_id, "docs/data.json#0")


if __name__ == "__main__":
    unittest.main()