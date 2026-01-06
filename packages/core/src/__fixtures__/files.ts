/**
 * Sample file content fixtures for ingestion testing
 *
 * Provides realistic file content for various file types.
 */

/**
 * Sample markdown documentation file
 */
export const MARKDOWN_FILE = `# Memory Consolidation

Memory consolidation is the process by which short-term memories are transformed into long-term memories.

## Sleep and Memory

Research shows that sleep plays a crucial role in memory consolidation. During sleep:

- Episodic memories are replayed
- Connections are strengthened
- Semantic abstractions are formed

## Consolidation Levels

Atlas uses hierarchical consolidation:

1. **Raw chunks** (level 0): Fresh ingestion
2. **Deduplicated** (level 1): Merged near-duplicates
3. **Topic summaries** (level 2): Aggregated themes
4. **Domain knowledge** (level 3): Abstract principles
`

/**
 * Sample TypeScript code file
 */
export const TYPESCRIPT_FILE = `/**
 * Embedding service for Atlas
 */

import type { EmbeddingBackend } from './types'

export class EmbeddingService {
  constructor(private backend: EmbeddingBackend) {}

  /**
   * Embed text content
   */
  async embedText(input: string | string[]): Promise<number[][]> {
    const inputs = Array.isArray(input) ? input : [input]
    const result = await this.backend.embedText(inputs)
    return result.embeddings
  }

  /**
   * Get embedding dimensions
   */
  getDimensions(): number {
    return this.backend.dimensions
  }
}
`

/**
 * Sample Python code file
 */
export const PYTHON_FILE = `"""
Vector storage backend implementation
"""

from typing import List, Dict, Optional
import numpy as np

class VectorStore:
    """In-memory vector storage for testing"""

    def __init__(self, dimensions: int = 1024):
        self.dimensions = dimensions
        self.vectors: Dict[str, np.ndarray] = {}

    def upsert(self, id: str, vector: List[float]) -> None:
        """Store a vector"""
        if len(vector) != self.dimensions:
            raise ValueError(f"Expected {self.dimensions}D vector")
        self.vectors[id] = np.array(vector)

    def search(self, query: List[float], k: int = 10) -> List[tuple]:
        """Cosine similarity search"""
        query_vec = np.array(query)
        scores = {}

        for id, vec in self.vectors.items():
            similarity = np.dot(query_vec, vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(vec)
            )
            scores[id] = similarity

        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:k]
`

/**
 * Sample JSON configuration file
 */
export const JSON_FILE = `{
  "name": "atlas-core",
  "version": "1.0.0",
  "embedding": {
    "provider": "voyage",
    "model": "voyage-3-large",
    "dimensions": 1024
  },
  "storage": {
    "provider": "qdrant",
    "collection": "atlas-memory",
    "distance": "cosine"
  },
  "consolidation": {
    "enabled": true,
    "similarityThreshold": 0.95,
    "minOccurrences": 2
  }
}
`

/**
 * Sample YAML configuration file
 */
export const YAML_FILE = `name: atlas-core
version: 1.0.0

embedding:
  provider: voyage
  model: voyage-3-large
  dimensions: 1024

storage:
  provider: qdrant
  collection: atlas-memory
  distance: cosine

consolidation:
  enabled: true
  similarityThreshold: 0.95
  minOccurrences: 2
`

/**
 * Sample log file
 */
export const LOG_FILE = `[2025-12-30T10:00:00Z] INFO  Starting Atlas memory service
[2025-12-30T10:00:01Z] INFO  Connected to Qdrant at localhost:6333
[2025-12-30T10:00:02Z] INFO  Collection 'atlas-memory' initialized (1024D vectors)
[2025-12-30T10:05:30Z] WARN  High memory usage detected (85% utilization)
[2025-12-30T10:10:15Z] ERROR Memory consolidation failed: similarity threshold too strict
[2025-12-30T10:10:16Z] INFO  Retrying with relaxed threshold (0.90)
[2025-12-30T10:10:17Z] INFO  Consolidation completed: 42 chunks merged into 18
[2025-12-30T11:00:00Z] INFO  Daily consolidation complete
`

/**
 * Sample shell script
 */
export const SHELL_FILE = `#!/bin/bash
# Atlas service startup script

set -euo pipefail

# Check dependencies
command -v bun >/dev/null 2>&1 || { echo "bun required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "docker required"; exit 1; }

# Start Qdrant container
docker compose up -d qdrant

# Wait for Qdrant to be ready
echo "Waiting for Qdrant..."
until curl -sf http://localhost:6333/health >/dev/null; do
  sleep 1
done

# Start Atlas daemon
echo "Starting Atlas daemon..."
bun run daemon
`

/**
 * Map file extensions to sample content
 */
export const FILE_CONTENT_BY_TYPE: Record<string, string> = {
  '.md': MARKDOWN_FILE,
  '.ts': TYPESCRIPT_FILE,
  '.tsx': TYPESCRIPT_FILE,
  '.js': TYPESCRIPT_FILE,
  '.jsx': TYPESCRIPT_FILE,
  '.py': PYTHON_FILE,
  '.json': JSON_FILE,
  '.yaml': YAML_FILE,
  '.yml': YAML_FILE,
  '.log': LOG_FILE,
  '.sh': SHELL_FILE,
  '.txt': MARKDOWN_FILE, // Use markdown as plain text sample
}

/**
 * Get sample content for a file path
 */
export function getSampleContent(filePath: string): string {
  const ext = filePath.slice(filePath.lastIndexOf('.')).toLowerCase()
  return FILE_CONTENT_BY_TYPE[ext] || MARKDOWN_FILE
}

/**
 * Create a temporary file path for testing
 */
export function createTestFilePath(name: string, ext: string): string {
  return `/tmp/atlas-test/${name}${ext}`
}

/**
 * Sample file paths for ingestion tests
 */
export const TEST_FILES = {
  markdown: '/test/docs/consolidation.md',
  typescript: '/test/src/embedding.ts',
  python: '/test/lib/vector_store.py',
  json: '/test/config/atlas.json',
  yaml: '/test/config/atlas.yaml',
  log: '/test/logs/2025-12-30.log',
  shell: '/test/scripts/start.sh',
} as const
