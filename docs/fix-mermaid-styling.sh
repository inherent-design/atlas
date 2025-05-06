#!/bin/bash

# Script to remove inline styling from Mermaid diagrams
# Run from the docs directory

# Find all Markdown files
find . -name "*.md" -type f | while read -r file; do
  echo "Processing $file..."
  
  # Remove classDef lines in mermaid blocks
  sed -i '' '/```mermaid/,/```/ {
    /classDef.*fill:/d
  }' "$file"
  
  # Remove class assignment lines in mermaid blocks
  sed -i '' '/```mermaid/,/```/ {
    /class.*data/d
    /class.*process/d
    /class.*component/d
    /class.*agent/d
    /class.*terminal/d
    /class.*philosophy/d
    /class.*application/d
  }' "$file"
  
  # Remove any lingering style-related lines in mermaid blocks
  sed -i '' '/```mermaid/,/```/ {
    /style/d
  }' "$file"

done

echo "Done removing Mermaid inline styling from all markdown files."