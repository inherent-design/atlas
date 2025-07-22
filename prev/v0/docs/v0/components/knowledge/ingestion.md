---

title: Document Ingestion

---


# Document Ingestion

This document explains the document ingestion system in Atlas, which processes documents into a format suitable for vector storage and semantic retrieval.

## Overview

The document ingestion system in Atlas is responsible for:

1. **Document Discovery**: Finding and loading documents from the filesystem
2. **Content Processing**: Parsing and splitting document content into appropriate chunks
3. **Metadata Extraction**: Deriving metadata from file paths and content
4. **Version Detection**: Identifying document versions from directory structure
5. **Embedding Generation**: Creating vector embeddings for document chunks
6. **Database Storage**: Storing embeddings and metadata in ChromaDB

The system is designed to handle a variety of document formats, with special optimizations for markdown files, and to maintain semantic coherence across document chunks.

## Core Components

### DocumentProcessor Class

The `DocumentProcessor` class is the central component of the ingestion system, responsible for managing the entire ingestion pipeline:

```python
from atlas.knowledge.ingest import DocumentProcessor

# Initialize the processor
processor = DocumentProcessor(
    anthropic_api_key=None,  # Optional, defaults to environment variable
    collection_name="atlas_knowledge_base",  # Optional, defaults to this value
    db_path=None,  # Optional, defaults to ~/atlas_chroma_db
)

# Process a directory of documents
processor.process_directory("/path/to/documents", recursive=True)
```

#### Constructor Parameters

| Parameter           | Type            | Description                            | Default                          |
| ------------------- | --------------- | -------------------------------------- | -------------------------------- |
| `anthropic_api_key` | `Optional[str]` | API key for Anthropic (for embeddings) | From `ANTHROPIC_API_KEY` env var |
| `collection_name`   | `str`           | Name of ChromaDB collection            | `"atlas_knowledge_base"`         |
| `db_path`           | `Optional[str]` | Path to ChromaDB storage               | `~/atlas_chroma_db`              |

#### Key Methods

- `process_directory()`: Processes all documents in a directory
- `process_markdown_file()`: Processes a single markdown file
- `generate_embeddings()`: Creates and stores embeddings for document chunks

### Document Processing Pipeline

#### 1. Document Discovery

The system provides methods to find documents in the filesystem:

```python
# Get all markdown files in a directory (recursively)
markdown_files = processor.get_all_markdown_files("/path/to/docs")

# Skip files that match .gitignore patterns
filtered_files = [f for f in markdown_files if not processor.is_ignored(f)]
```

The `.gitignore` pattern support ensures that temporary files, build artifacts, and other non-documentation files are excluded from ingestion.

#### 2. Content Chunking

Documents are split into semantic chunks that balance coherence with manageable size:

```python
# Split document by headings
sections = processor._split_by_headings(content, file_path)

# Each section has a title and text
for section in sections:
    title = section["title"]
    text = section["text"]
    # Process each section...
```

The chunking strategy follows these rules:

1. **Heading-Based Splitting**: Documents are primarily split by markdown headings (e.g., `# Heading`)
2. **Section Coherence**: Each section includes its heading and all content until the next heading
3. **Large Section Handling**: Sections exceeding a size threshold are further split into smaller chunks
4. **Fallback Strategy**: Documents without headings are split based on size alone

#### 3. Metadata Extraction

Each document chunk is enriched with metadata:

```python
# Extract metadata from the file path and content
metadata = {
    "path": rel_path,
    "source": rel_path,
    "file_name": os.path.basename(file_path),
    "section_title": section["title"],
    "version": version,
    "chunk_size": len(section["text"]),
}
```

This metadata provides crucial context for later retrieval and filtering.

#### 4. Version Detection

The system automatically extracts version information from file paths:

```python
# Extract version from path (e.g., v1, v2, v3)
version_match = re.search(r"/v(\d+(?:\.\d+)?)/", file_path)
version = version_match.group(1) if version_match else "current"
```

This enables versioned documentation storage and retrieval.

#### 5. Database Storage

Finally, document chunks and their metadata are stored in ChromaDB:

```python
# Prepare data for Chroma
ids = [chunk["id"] for chunk in chunks]
texts = [chunk["text"] for chunk in chunks]
metadatas = [chunk["metadata"] for chunk in chunks]

# Add data to Chroma collection
self.collection.add(ids=ids, documents=texts, metadatas=metadatas)
```

## Document Representation

Each document after processing is represented as:

```python
{
    "id": "knowledge/framework.md#2",  # Simplified ID (parent_dir/filename#chunk)
    "text": "# Entity Types\n\nThe Atlas knowledge graph...",  # Actual document content
    "metadata": {
        "source": "docs/knowledge/framework.md",  # Full relative file path
        "simple_id": "knowledge/framework.md",    # Simplified ID for readability
        "file_name": "framework.md",  # File name
        "section_title": "Entity Types",  # Section title
        "version": "3",  # Version (if detected)
        "chunk_size": 1024,  # Content length in characters
    },
}
```

This rich representation enables:

- **Precise Source Attribution**: Tracking where information came from
- **Section Navigation**: Understanding document structure
- **Version Control**: Managing documentation across different versions
- **Size Awareness**: Considering chunk size during retrieval

## Chunking Strategy

### Heading-Based Chunking

The default chunking strategy uses markdown headings as natural document boundaries:

```markdown
# Main Heading

Content under main heading...

## Subheading A

Content under subheading A...

## Subheading B

Content under subheading B...
```

This document would be split into three chunks:
1. "Main Heading" + content
2. "Subheading A" + content
3. "Subheading B" + content

The approach preserves the semantic structure of the document and maintains context within each section.

### Size Limitations

To prevent excessively large chunks, the system includes size-based checks:

```python
# Check for very large sections and warn
if len(section_text) > 5000:
    print(f"Warning: Large section in {file_path}: '{title}' ({len(section_text)} chars)")
```

Large sections are still processed as a single chunk, but a warning is logged. This approach balances semantic coherence (keeping related content together) with vector database limitations.

### Fallback Chunking

For documents without headings:

```python
# If content is very large, warn about it
if content_size > max_chunk_size * 5:
    print(f"Warning: Large document without headings ({content_size} chars)")
    print(f"Splitting into {(content_size // max_chunk_size) + 1} chunks")

if content_size <= max_chunk_size:
    # For small documents, keep as one chunk
    sections.append({"title": "Document", "text": content})
else:
    # Split large document into chunks
    for i in range(0, content_size, max_chunk_size):
        chunk = content[i : i + max_chunk_size]
        sections.append({
            "title": f"Document (Part {i // max_chunk_size + 1})",
            "text": chunk,
        })
```

This ensures that even large, unstructured documents can be processed effectively.

## File Type Support

Currently, the ingestion system is primarily optimized for:

- **Markdown (.md) files**: Full support with heading-based chunking
- **Text files**: Processed with fallback chunking

Future extensions could include support for:
- PDF documents
- HTML content
- Office documents (DOCX, PPTX, etc.)
- Code files with specialized chunking

## Integration with ChromaDB

The system integrates with ChromaDB for vector storage and retrieval:

```python
self.chroma_client = chromadb.PersistentClient(path=self.db_path)
self.collection = self.chroma_client.get_or_create_collection(name=collection_name)
```

Key aspects of the integration:

1. **Persistent Storage**: Document embeddings are stored on disk
2. **Collection-Based Organization**: Embeddings are organized in named collections
3. **Error Handling**: Graceful fallback to in-memory storage if persistence fails
4. **Embedding Generation**: Automatic generation of embeddings from text

## Progress Indicators and Reporting

The ingestion system provides comprehensive progress indicators to give visibility into the ingestion process:

### File Processing Progress

```
Processing files:
==================================================
[########################################] 100% Complete!
==================================================
```

During file processing, the system displays:
- A visual progress bar showing percentage completion
- Current file being processed with counter (e.g., "Processing: file.md (5/54)")
- Clear completion indicators with 100% marker

### Embedding Generation Progress

```
Embedding Generation:
==================================================
Total chunks to embed: 158
Estimated tokens: ~63,200
Estimated time: ~4.2 seconds
--------------------------------------------------
✓ Embedding completed in 4.12s
✓ Database storage completed in 0.78s
✓ Total processing time: 5.03s
✓ Throughput: 31.4 chunks/second
✓ Added 158 document chunks to Chroma DB
==================================================
```

During embedding generation, the system reports:
- Total chunks being embedded
- Token count estimation
- Estimated processing time
- Real-time progress with a spinner animation
- Detailed performance metrics after completion

### Final Processing Summary

```
Final Processing Summary:
==================================================
✓ Files processed:       54
✓ Chunks created:        158
✓ New documents added:   158
✓ Collection total size: 2039 documents
✓ Duplicates detected:   3
==================================================
```

The final summary provides:
- Total files processed
- Total chunks created and added
- Current collection size
- Duplicate detection statistics

## .gitignore Integration

The system includes integration with `.gitignore` patterns:

```python
def _load_gitignore(self) -> pathspec.PathSpec:
    """Load the gitignore patterns from the repository."""
    gitignore_patterns = []

    # Default ignore patterns
    default_patterns = [
        "node_modules/",
        ".git/",
        "__pycache__/",
        # More default patterns...
    ]

    # Add patterns from .gitignore file
    gitignore_path = os.path.join(os.getcwd(), ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    gitignore_patterns.append(line)

    # Create PathSpec with patterns
    return pathspec.PathSpec.from_lines("gitwildmatch", gitignore_patterns)
```

This ensures that temporary files, build artifacts, and other ignored files are not included in the knowledge base.

## Command-Line Interface

The document ingestion system can be used directly through the Atlas CLI:

```bash
# Ingest documents from a specific directory
python main.py -m ingest -d /path/to/docs -r

# Use a custom collection name and database path
python main.py -m ingest -d /path/to/docs -c custom_collection --db-path /custom/db/path
```

Options:
- `-d/--directory`: Directory to ingest documents from
- `-r/--recursive`: Recursively process subdirectories
- `-c/--collection`: Custom collection name
- `--db-path`: Custom database path

## Usage Examples

### Basic Directory Processing

```python
from atlas.knowledge.ingest import DocumentProcessor

# Initialize processor with default settings
processor = DocumentProcessor()

# Process a directory with markdown files
processor.process_directory("./documentation", recursive=True)

print(f"Successfully processed documents into the default collection")
```

### Custom Collection and DB Path

```python
from atlas.knowledge.ingest import DocumentProcessor
import os

# Create custom DB path
db_path = os.path.expanduser("~/my_custom_db")
os.makedirs(db_path, exist_ok=True)

# Initialize processor with custom settings
processor = DocumentProcessor(
    collection_name="project_docs",
    db_path=db_path
)

# Process documentation
processor.process_directory("./project_documentation")
processor.process_directory("./api_documentation")

# Get final document count
final_count = processor.collection.count()
print(f"Collection 'project_docs' now contains {final_count} document chunks")
```

### Processing Multiple Version Directories

```python
from atlas.knowledge.ingest import DocumentProcessor

# Initialize processor
processor = DocumentProcessor(collection_name="versioned_docs")

# Process each version directory
version_dirs = [
    "./docs/v1",
    "./docs/v2",
    "./docs/v3",
]

for directory in version_dirs:
    if os.path.exists(directory):
        print(f"Processing version: {directory}")
        processor.process_directory(directory, recursive=True)

# Show version distribution
print("Document distribution by version:")
all_docs = processor.collection.get(limit=processor.collection.count())
versions = {}
for metadata in all_docs["metadatas"]:
    version = metadata.get("version", "unknown")
    versions[version] = versions.get(version, 0) + 1

for version, count in versions.items():
    print(f"  - Version {version}: {count} chunks")
```

### Processing a Single File

```python
from atlas.knowledge.ingest import DocumentProcessor

# Initialize processor
processor = DocumentProcessor()

# Process a single markdown file
file_path = "./important_document.md"
chunks = processor.process_markdown_file(file_path)

print(f"Processed {file_path} into {len(chunks)} chunks:")
for i, chunk in enumerate(chunks):
    title = chunk["metadata"]["section_title"]
    size = chunk["metadata"]["chunk_size"]
    print(f"  {i+1}. {title} ({size} chars)")

# Store the chunks
processor.generate_embeddings(chunks)
```

### Using the Example Script

Atlas includes an example script that demonstrates the enhanced document ingestion features:

```python
# Example from examples/ingest_example.py
import argparse
from atlas.knowledge.ingest import DocumentProcessor

def main():
    parser = argparse.ArgumentParser(description="Ingest documents with progress indicators")
    parser.add_argument("-d", "--directory", type=str, default="./docs",
                        help="Directory containing documents to ingest")
    parser.add_argument("-c", "--collection", type=str, default="atlas_knowledge_base",
                        help="Collection name for document storage")
    parser.add_argument("--recursive", action="store_true", default=True,
                        help="Process subdirectories recursively")

    args = parser.parse_args()

    # Create document processor
    processor = DocumentProcessor(collection_name=args.collection)

    # Process the directory with progress indicators
    processor.process_directory(args.directory, recursive=args.recursive)

    print("\nIngestion complete!")

if __name__ == "__main__":
    main()
```

Run this example with:

```bash
python -m examples.ingest_example -d ./docs
```

Additionally, you can verify the document ID format with the `verify_document_ids.py` example:

```bash
python -m examples.verify_document_ids
```

This will sample document IDs from your collection and verify they're using the simplified format.

## Best Practices

### Document Preparation

For optimal results when preparing documents for ingestion:

1. **Use Clear Headings**: Structure documents with meaningful markdown headings
2. **Heading Hierarchy**: Use appropriate heading levels (# for main sections, ## for subsections)
3. **Semantic Sections**: Keep related content under the same heading
4. **Reasonable Section Size**: Aim for sections around 1,000-3,000 characters
5. **Informative Titles**: Use descriptive heading titles that convey section content
6. **Version Organization**: Use version directories (e.g., v1/, v2/) for versioned documentation

### Ingestion Process

For the most effective ingestion process:

1. **Batch Processing**: Process related documents in batches for consistency
2. **Database Management**: Use a single database path for related collections
3. **Collection Organization**: Use separate collections for different document domains
4. **Resource Management**: Monitor memory usage for very large document sets
5. **Error Checking**: Verify document count after ingestion to confirm success

## Troubleshooting

### Empty Collections

If the collection remains empty after ingestion:

1. Check that documents exist in the specified directory
2. Verify file extensions (currently optimized for .md files)
3. Ensure files are not being filtered by .gitignore patterns
4. Check if there are any errors during the chunking process

### Large Document Warnings

If you see warnings about large documents or sections:

1. Consider restructuring the document with more headings
2. Split very large sections into multiple smaller sections
3. For documents without headings, consider adding heading structure

### Database Access Errors

If you encounter errors accessing the ChromaDB:

1. Verify the database path exists and is writable
2. Check disk space availability
3. Ensure no other processes have exclusive access to the database

## Related Documentation

- [Knowledge System Overview](./) - Overview of the knowledge management system
- [Retrieval System](./retrieval.md) - Information about knowledge retrieval functionality
- [ChromaDB Documentation](https://docs.trychroma.com/) - Official ChromaDB documentation
