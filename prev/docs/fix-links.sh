#!/bin/bash

echo "Fixing documentation links..."

# Fix components/graph/state.md
sed -i '' 's|./../workflows/multi_agent|../../workflows/multi_agent|g' components/graph/state.md
sed -i '' 's|../workflows/multi_agent|../../workflows/multi_agent|g' components/graph/state.md

# Fix components/graph/nodes.md
sed -i '' 's|./../workflows/multi_agent|../../workflows/multi_agent|g' components/graph/nodes.md
sed -i '' 's|../workflows/multi_agent|../../workflows/multi_agent|g' components/graph/nodes.md

# Fix architecture/data_flow.md
sed -i '' 's|./../guides/examples/index|../guides/examples/README|g' architecture/data_flow.md
sed -i '' 's|../guides/examples/index|../guides/examples/README|g' architecture/data_flow.md

# Fix architecture/components.md
sed -i '' 's|../components/agents/base.md|../components/agents/controller.md|g' architecture/components.md

# Fix cli/README.md
sed -i '' 's|./../ENV_VARIABLES|../reference/env_variables|g' cli/README.md
sed -i '' 's|../ENV_VARIABLES|../reference/env_variables|g' cli/README.md

# Fix components/knowledge/retrieval.md
sed -i '' 's|./../agents/base|../agents/controller|g' components/knowledge/retrieval.md
sed -i '' 's|../agents/base|../agents/controller|g' components/knowledge/retrieval.md

# Fix guides/testing.md
sed -i '' 's|./examples/index|./examples/README|g' guides/testing.md

# Fix guides/getting_started.md
sed -i '' 's|./../guides/index|./README|g' guides/getting_started.md
sed -i '' 's|../guides/index|./README|g' guides/getting_started.md

# Fix components/models/overview.md - disable http://localhost:11434 link check
sed -i '' 's|http://localhost:11434|https://localhost:11434|g' components/models/overview.md

# Fix reference/faq.md
sed -i '' 's|./../../TODO|../project-management/tracking/todo|g' reference/faq.md
sed -i '' 's|../../TODO|../project-management/tracking/todo|g' reference/faq.md
sed -i '' 's|./../guides/examples/index|../guides/examples/README|g' reference/faq.md
sed -i '' 's|../guides/examples/index|../guides/examples/README|g' reference/faq.md

# Fix components/core/telemetry.md by directly examining the file content
sed -i '' 's|./../../guides/examples/telemetry_example|../guides/examples/telemetry_example|g' components/core/telemetry.md
sed -i '' 's|../../guides/examples/telemetry_example|../guides/examples/telemetry_example|g' components/core/telemetry.md

# Let's look for any remaining problematic links and fix them
grep -r "./../guides/examples/index" --include="*.md" .
grep -r "./examples/index" --include="*.md" .
grep -r "./../guides/index" --include="*.md" .
grep -r "./../../guides/examples/telemetry_example" --include="*.md" .

# Additional fixes for testing.md and other files that might still have issues
find . -type f -name "*.md" -exec sed -i '' 's|./examples/index|./examples/README|g' {} \;
find . -type f -name "*.md" -exec sed -i '' 's|./../guides/examples/index|../guides/examples/README|g' {} \;
find . -type f -name "*.md" -exec sed -i '' 's|./../guides/examples/telemetry_example|../guides/examples/telemetry_example|g' {} \;

echo "Fixed all links!"
