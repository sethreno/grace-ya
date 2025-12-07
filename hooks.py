"""MkDocs hooks to automatically generate Bible verse links."""

import re
import urllib.parse


def on_page_markdown(markdown, **kwargs):
    """Convert Bible verse references into BibleGateway links.

    Matches patterns like:
    - John 3:16
    - 1 John 4:16
    - Genesis 2:18-24
    - Colossians 1:9–12 (with en dash)

    Only converts them if they appear as list items (- Reference)
    """

    def verse_to_link(match):
        """Convert a verse reference to a BibleGateway link."""
        verse_text = match.group(1).strip()

        # URL encode the verse reference for BibleGateway
        search_query = urllib.parse.quote(verse_text.lower())
        url = f"https://www.biblegateway.com/passage/?search={search_query}&version=NIV"

        return f"- [{verse_text}]({url})"

    # Pattern to match list items with Bible verses
    # Matches: - Book Chapter:Verse or - Book Chapter:Verse-Verse
    # Books can have numbers (1 John, 2 Corinthians) and multiple words (Song of Solomon)
    pattern = r'^(\s*)- ([0-9]?\s?[A-Za-z]+(?:\s+of\s+[A-Za-z]+)?\s+\d+:\d+(?:[-–]\d+)?)\s*$'

    lines = markdown.split('\n')
    processed_lines = []

    for line in lines:
        match = re.match(pattern, line)
        if match:
            indent = match.group(1)
            verse_text = match.group(2).strip()

            # URL encode the verse reference for BibleGateway
            search_query = urllib.parse.quote(verse_text.lower())
            url = f"https://www.biblegateway.com/passage/?search={search_query}&version=NIV"

            processed_lines.append(f"{indent}- [{verse_text}]({url}){{:target=\"_blank\"}}")
        else:
            processed_lines.append(line)

    return '\n'.join(processed_lines)
