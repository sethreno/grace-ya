# Building the Grace Young Adults Website

This site uses **MkDocs** with the Material theme to convert markdown content into beautiful HTML.

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Edit Content
Edit markdown files in the `docs/` directory:
- `docs/index.md` - Main homepage content

### Preview the Site
Run a live preview server that auto-reloads when you save changes:
```bash
mkdocs serve
```
Then open http://127.0.0.1:8000 in your browser.

### Build the Site
Generate the HTML files:
```bash
mkdocs build
```
or use the build script:
```bash
bash build.sh
```

The generated HTML will be in the `site/` directory.

### Deploy
To deploy to GitHub Pages:
```bash
mkdocs gh-deploy
```

## Customization

### Change Theme Colors
Edit `mkdocs.yml` and modify the `theme.palette.primary` and `theme.palette.accent` values.
Available colors: red, pink, purple, deep purple, indigo, blue, light blue, cyan, teal, green, light green, lime, yellow, amber, orange, deep orange

### Add New Pages
1. Create a new markdown file in `docs/` (e.g., `docs/about.md`)
2. Add it to the navigation in `mkdocs.yml`:
   ```yaml
   nav:
     - Home: index.md
     - About: about.md
   ```

## Why MkDocs?

- ✅ Python-based (easy to install and customize)
- ✅ Beautiful built-in themes (Material theme included)
- ✅ Live preview server
- ✅ Write content in simple markdown
- ✅ Automatic navigation and search
- ✅ Mobile-friendly responsive design
- ✅ Dark mode support
