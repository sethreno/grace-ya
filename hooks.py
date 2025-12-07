"""MkDocs hooks to automatically generate Bible verse links and QR codes."""

import re
import urllib.parse
import os
import qrcode


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


def on_pre_build(config, **kwargs):
    """Generate QR code for the site homepage before building."""
    site_url = "https://sethreno.github.io/grace-ya/"

    # Create assets directory if it doesn't exist
    source_dir = config['docs_dir']
    assets_dir = os.path.join(source_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(site_url)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="white")

    # Save QR code
    qr_path = os.path.join(assets_dir, 'qr-code.png')
    img.save(qr_path)

    print(f"Generated QR code: {qr_path}")
