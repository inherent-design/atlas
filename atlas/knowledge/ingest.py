"""
Document ingestion for the Atlas framework.

This module handles processing Atlas documentation into a format
suitable for vector storage and retrieval.
"""

import os
import re
import glob
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
import pathspec
from anthropic import Anthropic


class DocumentProcessor:
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        db_path: Optional[str] = None,
    ):
        """Initialize the document processor.

        Args:
            anthropic_api_key: Optional API key for Anthropic. If not provided,
                              it will be read from the ANTHROPIC_API_KEY environment variable.
            collection_name: Name of the Chroma collection to use.
            db_path: Optional path for ChromaDB storage. If None, use default in home directory.
        """
        self.anthropic_client = Anthropic(
            api_key=anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        )

        # Create an absolute path for ChromaDB storage (use provided or default to home directory)
        if db_path:
            self.db_path = db_path
        else:
            home_dir = Path.home()
            db_path_obj = home_dir / "atlas_chroma_db"
            db_path_obj.mkdir(exist_ok=True)
            self.db_path = str(db_path_obj.absolute())

        print(f"ChromaDB persistence directory: {self.db_path}")

        # List contents of directory to debug
        print("Current contents of DB directory:")
        try:
            for item in os.listdir(self.db_path):
                item_path = os.path.join(self.db_path, item)
                if os.path.isdir(item_path):
                    print(f"  - {item}/ (directory)")
                else:
                    size = os.path.getsize(item_path) / 1024  # Size in KB
                    print(f"  - {item} ({size:.2f} KB)")
        except Exception as e:
            print(f"Error listing DB directory: {e}")

        try:
            self.chroma_client = chromadb.PersistentClient(path=self.db_path)
            print(
                f"ChromaDB client initialized successfully with persistence at: {self.db_path}"
            )

            # List all collections
            try:
                all_collections = self.chroma_client.list_collections()
                print(f"Available collections: {[c.name for c in all_collections]}")
            except Exception as e:
                print(f"Error listing collections: {e}")

            # Get or create collection
            try:
                self.collection = self.chroma_client.get_or_create_collection(
                    name=collection_name
                )
                print(f"Collection '{collection_name}' accessed successfully")

                # Get initial document count
                self.initial_doc_count = self.collection.count()
                print(
                    f"Collection initially contains {self.initial_doc_count} documents"
                )

                if self.initial_doc_count == 0:
                    print(
                        "NOTE: Collection is empty. Documents will be ingested from scratch."
                    )
            except Exception as e:
                print(f"Error accessing collection: {e}")
                raise e

        except Exception as e:
            print(f"Error initializing ChromaDB: {str(e)}")
            # Fallback to in-memory if persistence fails
            print("Falling back to in-memory ChromaDB")
            self.chroma_client = chromadb.Client()
            self.collection = self.chroma_client.get_or_create_collection(
                name=collection_name
            )
            self.initial_doc_count = 0

        self.gitignore_spec = self._load_gitignore()

    def _load_gitignore(self) -> pathspec.PathSpec:
        """Load the gitignore patterns from the repository.

        Returns:
            A PathSpec object with the gitignore patterns.
        """
        gitignore_patterns = []

        # Default ignore patterns (common files to ignore regardless of .gitignore)
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
                print(
                    f"Loaded {len(gitignore_patterns) - len(default_patterns)} patterns from .gitignore"
                )
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
            print(
                f"Excluded {len(all_md_files) - len(filtered_files)} files due to gitignore patterns"
            )

        return filtered_files

    def process_markdown_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Process a markdown file into chunks suitable for vector storage.

        Args:
            file_path: Path to the markdown file.

        Returns:
            A list of document chunks with metadata.
        """
        # Skip processing if file is in gitignore
        if self.is_ignored(file_path):
            print(f"Skipping ignored file: {file_path}")
            return []

        print(f"Processing file: {file_path}")

        # Check file size and warn if it's very large
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 10:
            print(
                f"Warning: Processing large file ({file_size_mb:.1f} MB): {file_path}"
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {str(e)}")
            return []

        # Extract document sections based on headings
        sections = self._split_by_headings(content, file_path)

        # Create document chunks with metadata
        chunks = []
        rel_path = os.path.relpath(file_path, start=os.getcwd())
        file_name = os.path.basename(file_path)

        # Extract version from path (e.g., v1, v2, v3)
        version_match = re.search(r"/v(\d+(?:\.\d+)?)/", file_path)
        version = version_match.group(1) if version_match else "current"

        for i, section in enumerate(sections):
            section_id = f"{rel_path}#{i}"

            chunks.append(
                {
                    "id": section_id,
                    "text": section["text"],
                    "metadata": {
                        "path": rel_path,  # Add path field
                        "source": rel_path,
                        "file_name": file_name,
                        "section_title": section["title"],
                        "version": version,
                        "chunk_size": len(section["text"]),
                    },
                }
            )

        return chunks

    def _split_by_headings(
        self, content: str, file_path: str = ""
    ) -> List[Dict[str, str]]:
        """Split markdown content by headings.

        Args:
            content: The markdown content.
            file_path: Optional file path for logging purposes.

        Returns:
            A list of sections with titles and text.
        """
        # Match headings with the following pattern: one or more #'s followed by text
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

        # Find all headings
        headings = list(heading_pattern.finditer(content))

        sections = []

        # If no headings, treat the entire document as one section
        if not headings:
            # For large documents without headings, split into multiple chunks
            content_size = len(content)
            max_chunk_size = (
                2000  # Arbitrary chunk size to prevent extremely large chunks
            )

            # If content is very large, warn about it
            if content_size > max_chunk_size * 5:
                print(
                    f"Warning: Large document without headings ({content_size} chars): {file_path}"
                )
                print(f"  Splitting into {(content_size // max_chunk_size) + 1} chunks")

            if content_size <= max_chunk_size:
                sections.append({"title": "Document", "text": content})
            else:
                # Split large document into chunks
                for i in range(0, content_size, max_chunk_size):
                    chunk = content[i : i + max_chunk_size]
                    sections.append(
                        {
                            "title": f"Document (Part {i // max_chunk_size + 1})",
                            "text": chunk,
                        }
                    )

            return sections

        # Process each section defined by headings
        for i, match in enumerate(headings):
            title = match.group(2).strip()
            start_pos = match.start()

            # Determine end position (start of next heading or end of document)
            if i < len(headings) - 1:
                end_pos = headings[i + 1].start()
            else:
                end_pos = len(content)

            # Get section text including the heading
            section_text = content[start_pos:end_pos].strip()

            # Check for very large sections and warn
            if len(section_text) > 5000:
                print(
                    f"Warning: Large section in {file_path}: '{title}' ({len(section_text)} chars)"
                )

            sections.append({"title": title, "text": section_text})

        return sections

    def generate_embeddings(self, chunks: List[Dict[str, Any]]) -> None:
        """Generate embeddings for document chunks and store them in Chroma.

        Args:
            chunks: List of document chunks with metadata.
        """
        if not chunks:
            return

        # Prepare data for Chroma
        ids = [chunk["id"] for chunk in chunks]
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        # Add data to Chroma collection
        try:
            self.collection.add(ids=ids, documents=texts, metadatas=metadatas)
            print(f"Added {len(chunks)} document chunks to Chroma DB")
        except Exception as e:
            print(f"Error adding documents to ChromaDB: {e}")
            print(f"Stack trace: {sys.exc_info()[2]}")

    def process_directory(self, directory: str, recursive: bool = True) -> None:
        """Process all markdown files in a directory and its subdirectories.

        Args:
            directory: The directory to process.
            recursive: Whether to recursively process subdirectories.
        """
        files = (
            self.get_all_markdown_files(directory)
            if recursive
            else glob.glob(f"{directory}/*.md")
        )
        print(f"Found {len(files)} markdown files to process in {directory}")

        all_chunks = []
        for file_path in files:
            chunks = self.process_markdown_file(file_path)
            all_chunks.extend(chunks)

        self.generate_embeddings(all_chunks)

        # Report final stats
        try:
            final_doc_count = self.collection.count()
            new_docs = final_doc_count - self.initial_doc_count
            print(
                f"Successfully processed {len(files)} files into {len(all_chunks)} chunks"
            )
            print(
                f"Added {new_docs} new documents to collection (now contains {final_doc_count} total)"
            )
        except Exception as e:
            print(f"Error getting final collection stats: {e}")


def main():
    """Main function to ingest Atlas documentation."""
    processor = DocumentProcessor()

    # Process each version directory
    src_dirs = [
        "./src-markdown/prev/v1",
        "./src-markdown/prev/v2",
        "./src-markdown/prev/v3",
        "./src-markdown/prev/v4",
        "./src-markdown/prev/v5",
        "./src-markdown/quantum",
    ]

    for directory in src_dirs:
        if os.path.exists(directory):
            print(f"Processing directory: {directory}")
            processor.process_directory(directory)


if __name__ == "__main__":
    main()
