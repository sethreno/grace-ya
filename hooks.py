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

# Private-use Unicode sentinels for words of Christ (U+E000/E001 never appear in Bible text)
_WOC_START = ''
_WOC_END = ''


@_cache.memoize()
def fetch_verse_html(verse_reference, version='NIV'):
    """Fetch and cache the raw passage-text div HTML from BibleGateway.

    Caching raw HTML means processing logic can change (e.g. woc marking,
    text cleaning) without requiring new HTTP requests.
    """
    try:
        search_query = urllib.parse.quote(verse_reference.lower())
        url = f"https://www.biblegateway.com/passage/?search={search_query}&version={version}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        passage_div = soup.find('div', class_='passage-text')
        if not passage_div:
            print(f"Warning: Could not find passage text for {verse_reference} ({version})")
            return None

        print(f"Fetched HTML for {verse_reference} ({version})")
        return str(passage_div)

    except Exception as e:
        print(f"Error fetching verse {verse_reference}: {e}")
        return None


def process_verse_html(raw_html):
    """Process cached passage HTML into clean text with words-of-Christ markers.

    Returns text with _WOC_START/_WOC_END wrapping Jesus' words (from <span class="woc">).
    """
    soup = BeautifulSoup(raw_html, 'html.parser')
    passage_div = soup.find('div', class_='passage-text') or soup

    for sup in passage_div.find_all('sup'):
        sup.decompose()

    for div in passage_div.find_all('div', class_=['crossrefs', 'footnotes', 'full-chap-link']):
        div.decompose()

    for link in passage_div.find_all('a'):
        link.decompose()

    for heading in passage_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        heading.decompose()

    for woc in passage_div.find_all('span', class_='woj'):
        woc.replace_with(_WOC_START + woc.get_text(separator=' ', strip=True) + _WOC_END)

    def clean_text(text):
        text = re.sub(r'\([A-Z]\)', '', text)
        text = re.sub(r'\[[a-z]\]', '', text)
        text = re.sub(r'^\d+\s+', '', text)
        text = re.sub(r'the\s*Lord', 'the Lord', text, flags=re.IGNORECASE)
        text = re.sub(r'TheLord', 'The Lord', text)
        text = re.sub(r'\s+([,.:;!?])', r'\1', text)
        return re.sub(r'\s+', ' ', text).strip()

    paragraphs = [
        clean_text(p.get_text(separator=' ', strip=True))
        for p in passage_div.find_all('p')
    ]
    paragraphs = [p for p in paragraphs if p]

    if paragraphs:
        return '\n\n'.join(paragraphs)
    else:
        return clean_text(passage_div.get_text(separator=' ', strip=True))


def on_page_markdown(markdown, **kwargs):
    """Convert Bible verse references into BibleGateway links.

    Matches patterns like:
    - John 3:16
    - 1 John 4:16
    - Genesis 2:18-24
    - Colossians 1:9–12 (with en dash)

    Only converts them if they appear as list items (- Reference)
    """
    pattern = r'^(\s*)- ([0-9]?\s?[A-Za-z]+(?:\s+of\s+[A-Za-z]+)?\s+\d+:\d+(?:[-–]\d+)?)\s*$'

    lines = markdown.split('\n')
    processed_lines = []

    for line in lines:
        match = re.match(pattern, line)
        if match:
            indent = match.group(1)
            verse_ref = match.group(2).strip()

            search_query = urllib.parse.quote(verse_ref.lower())
            url = f"https://www.biblegateway.com/passage/?search={search_query}&version=NIV"

            translations = {}
            for version in VERSIONS:
                raw_html = fetch_verse_html(verse_ref, version)
                if raw_html:
                    text = process_verse_html(raw_html)
                    if text:
                        translations[version] = text

            if translations:
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

    source_dir = config['docs_dir']
    assets_dir = os.path.join(source_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(site_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    qr_path = os.path.join(assets_dir, 'qr-code.png')
    img.save(qr_path)

    print(f"Generated QR code: {qr_path}")
