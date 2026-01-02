#!/bin/bash

# Fix Markdown links ending with .md to remove the extension
# This makes the links compatible with VitePress best practices

DOCS_DIR="/Users/zer0cell/Production/Software/llm/atlas/docs"

echo "Fixing .md extensions in markdown links..."

# Use find and sed to replace all links ending with .md in all markdown files
# This pattern matches [link text](path/to/file.md) and changes it to [link text](path/to/file)
find "$DOCS_DIR" -name "*.md" -type f -exec sed -i '' -E 's/(\[[^]]+\]\([^)]+)\.md([^)]*\))/\1\2/g' {} \;

# Use grep to verify if there are any remaining .md links
remaining_links=$(grep -r "\\.md)" --include="*.md" "$DOCS_DIR" | wc -l)

if [ "$remaining_links" -eq 0 ]; then
  echo "Success! All .md extensions have been removed from markdown links."
else
  echo "Warning: There might still be some .md links remaining. Please check manually."
  grep -r "\\.md)" --include="*.md" "$DOCS_DIR"
fi

echo "Script completed. Please verify the changes with 'git diff' before committing."
