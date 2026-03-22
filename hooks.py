"""MkDocs hooks to automatically generate Bible verse links and QR codes."""

import re
import html
import urllib.parse
import os
import qrcode
import requests
import diskcache
from bs4 import BeautifulSoup

_cache = diskcache.Cache('.verse_cache')

VERSIONS = ['CJB', 'ESV', 'NIV', 'NKJV', 'NLT']


@_cache.memoize()
def fetch_verse_text(verse_reference, version='NIV'):
    """Fetch verse text from BibleGateway.

    Args:
        verse_reference: Bible verse reference (e.g., "John 3:16")
        version: Bible version abbreviation (e.g., "NIV", "ESV")

    Returns:
        The verse text as a string, or None if fetching fails
    """
    try:
        # URL encode the verse reference for BibleGateway
        search_query = urllib.parse.quote(verse_reference.lower())
        url = f"https://www.biblegateway.com/passage/?search={search_query}&version={version}"

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

        def clean_text(text):
            text = re.sub(r'\([A-Z]\)', '', text)          # cross-reference markers (A), (B)
            text = re.sub(r'\[[a-z]\]', '', text)          # footnote markers [a], [b]
            text = re.sub(r'^\d+\s+', '', text)            # leading verse numbers
            text = re.sub(r'the\s*Lord', 'the Lord', text, flags=re.IGNORECASE)
            text = re.sub(r'TheLord', 'The Lord', text)
            text = re.sub(r'\s+([,.:;!?])', r'\1', text)  # spacing before punctuation
            return re.sub(r'\s+', ' ', text).strip()

        # Extract paragraphs individually to preserve paragraph breaks
        paragraphs = [
            clean_text(p.get_text(separator=' ', strip=True))
            for p in passage_div.find_all('p')
        ]
        paragraphs = [p for p in paragraphs if p]

        if paragraphs:
            result = '\n\n'.join(paragraphs)
        else:
            result = clean_text(passage_div.get_text(separator=' ', strip=True))

        print(f"Fetched verse text for {verse_reference} ({version}): {result[:50]}...")
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

            # Fetch verse text for all translations
            translations = {}
            for version in VERSIONS:
                text = fetch_verse_text(verse_ref, version)
                if text:
                    translations[version] = text

            # Build the markdown line with verse text if available
            if translations:
                # Encode newlines as &#10; so they survive HTML attribute parsing
                data_attrs = ' '.join(
                    f'data-{v.lower()}="{html.escape(t, quote=True).replace(chr(10), "&#10;")}"'
                    for v, t in translations.items()
                )
                default_text = translations.get('NIV', next(iter(translations.values())))
                initial_html = html.escape(default_text).replace('\n\n', '<br><br>')
                verse_span = f'<span class="verse-text" {data_attrs}>{initial_html}</span>'
                processed_lines.append(f"{indent}- [{verse_ref}]({url}){{:target=\"_blank\"}} - {verse_span}")
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
