#!/bin/bash
# Build script to generate HTML from markdown using MkDocs with uv

# Sync dependencies using uv
uv sync

# Build the site using uv
uv run mkdocs build

# Optional: Copy the generated index.html to root directory
# Uncomment the line below if you want to keep index.html in the root
# cp site/index.html ./index.html

echo "Site built successfully! Output is in the 'site' directory."
