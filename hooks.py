"""MkDocs hooks to automatically generate Bible verse links and QR codes."""

import re
import urllib.parse
import os
import qrcode
import requests
from bs4 import BeautifulSoup
from functools import lru_cache


@lru_cache(maxsize=128)
def fetch_verse_text(verse_reference):
    """Fetch verse text from BibleGateway.

    Args:
        verse_reference: Bible verse reference (e.g., "John 3:16")

    Returns:
        The verse text as a string, or None if fetching fails
    """
    try:
        # URL encode the verse reference for BibleGateway
        search_query = urllib.parse.quote(verse_reference.lower())
        url = f"https://www.biblegateway.com/passage/?search={search_query}&version=NIV"

        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the passage text div
        passage_div = soup.find('div', class_='passage-text')
        if not passage_div:
            print(f"Warning: Could not find passage text for {verse_reference}")
            return None

        # Remove superscript elements (verse numbers, cross-references, footnotes)
        for sup in passage_div.find_all('sup'):
            sup.decompose()

        # Remove cross-reference and footnote divs
        for div in passage_div.find_all('div', class_=['crossrefs', 'footnotes', 'full-chap-link']):
            div.decompose()

        # Remove links
        for link in passage_div.find_all('a'):
            link.decompose()

        # Remove headings (like "Warning to Pay Attention")
        for heading in passage_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading.decompose()

        # Get all text with proper spacing between elements
        result = passage_div.get_text(separator=' ', strip=True)

        # Clean up the result
        # Remove cross-reference markers like (A), (B), etc.
        result = re.sub(r'\([A-Z]\)', '', result)
        # Remove verse numbers at the beginning (e.g., "2 We must...")
        result = re.sub(r'^\d+\s+', '', result)
        # Fix spacing issues with "LORD"
        result = re.sub(r'the\s*Lord', 'the Lord', result, flags=re.IGNORECASE)
        # Fix "TheLord" -> "The Lord"
        result = re.sub(r'TheLord', 'The Lord', result)
        # Fix spacing before punctuation
        result = re.sub(r'\s+([,.:;!?])', r'\1', result)
        # Clean up multiple spaces
        result = re.sub(r'\s+', ' ', result).strip()

        print(f"Fetched verse text for {verse_reference}: {result[:50]}...")
        return result

    except Exception as e:
        print(f"Error fetching verse {verse_reference}: {e}")
        return None


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
            verse_ref = match.group(2).strip()

            # URL encode the verse reference for BibleGateway
            search_query = urllib.parse.quote(verse_ref.lower())
            url = f"https://www.biblegateway.com/passage/?search={search_query}&version=NIV"

            # Fetch the verse text
            verse_text = fetch_verse_text(verse_ref)

            # Build the markdown line with verse text if available
            if verse_text:
                processed_lines.append(f"{indent}- [{verse_ref}]({url}){{:target=\"_blank\"}} - *{verse_text}*")
            else:
                processed_lines.append(f"{indent}- [{verse_ref}]({url}){{:target=\"_blank\"}}")
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
