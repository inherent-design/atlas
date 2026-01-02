/**
 * Text Splitter (LangChain RecursiveCharacterTextSplitter)
 */

import { RecursiveCharacterTextSplitter } from '@langchain/textsplitters'
import { CHUNK_SIZE, CHUNK_OVERLAP, CHUNK_SEPARATORS } from '../../shared/config'

export function createTextSplitter(): RecursiveCharacterTextSplitter {
  return new RecursiveCharacterTextSplitter({
    chunkSize: CHUNK_SIZE,
    chunkOverlap: CHUNK_OVERLAP,
    separators: CHUNK_SEPARATORS,
  })
}

// Singleton instance (lazy initialization)
let textSplitterInstance: RecursiveCharacterTextSplitter | null = null

export function getTextSplitter(): RecursiveCharacterTextSplitter {
  if (!textSplitterInstance) {
    textSplitterInstance = createTextSplitter()
  }
  return textSplitterInstance
}

// For testing: reset singleton
export function resetTextSplitter(): void {
  textSplitterInstance = null
}
