const TRANSLATIONS = [
  { id: 'CJB', name: 'Complete Jewish Bible' },
  { id: 'ESV', name: 'English Standard Version' },
  { id: 'NIV', name: 'New International Version' },
  { id: 'NKJV', name: 'New King James Version' },
  { id: 'NLT', name: 'New Living Translation' },
];

const WOC_START = '';
const WOC_END = '';

function getCurrentTranslation() {
  return localStorage.getItem('bible-translation') || 'NIV';
}

function getRedLetters() {
  return localStorage.getItem('red-letters') !== 'false';
}

function applyRedLetters(enabled) {
  document.body.classList.toggle('hide-red-letters', !enabled);
}

function textToHtml(text) {
  const tmp = document.createElement('span');
  tmp.textContent = text;
  return tmp.innerHTML
    .replace(//g, '<span class="jesus-words">')
    .replace(//g, '</span>');
}

function setVerseText(el, text) {
  const parts = text.split('\n\n').map(textToHtml);
  el.innerHTML = parts.join('<br><br>');
}

function updateVerseTexts(version) {
  document.querySelectorAll('.verse-text').forEach(el => {
    const text = el.dataset[version.toLowerCase()];
    if (text) setVerseText(el, text);
  });
}

function updateVerseLinks(version) {
  document.querySelectorAll('a[href*="biblegateway.com/passage"]').forEach(link => {
    const url = new URL(link.href);
    url.searchParams.set('version', version);
    link.href = url.toString();
  });
}

function injectSelector() {
  if (document.getElementById('translation-select')) return;

  const style = document.createElement('style');
  style.textContent = `
    #translation-select option {
      background-color: var(--md-default-bg-color);
      color: var(--md-default-fg-color--light);
    }
    .jesus-words {
      color: #c0392b;
    }
    [data-md-color-scheme="slate"] .jesus-words {
      color: #e57373;
    }
    .hide-red-letters .jesus-words {
      color: inherit;
    }
    #red-letters-toggle {
      background: transparent;
      border: none;
      color: #c0392b;
      cursor: pointer;
      font-size: .9rem;
      font-weight: bold;
      font-family: Georgia, serif;
      padding: 0 .25rem;
      height: 1.5rem;
      line-height: 1.5rem;
    }
    #red-letters-toggle.off {
      color: var(--md-primary-bg-color);
      opacity: 0.45;
    }
  `;
  document.head.appendChild(style);

  const headerInner = document.querySelector('.md-header__inner');
  if (!headerInner) return;

  const current = getCurrentTranslation();
  const redLetters = getRedLetters();

  const select = document.createElement('select');
  select.id = 'translation-select';
  select.title = 'Bible Translation';
  select.style.cssText = [
    'background: transparent',
    'border: none',
    'color: var(--md-primary-bg-color)',
    'cursor: pointer',
    'font-size: .75rem',
    'font-family: inherit',
    'padding: 0 .25rem',
    'outline: none',
    'height: 1.5rem',
  ].join(';');

  TRANSLATIONS.forEach(t => {
    const option = document.createElement('option');
    option.value = t.id;
    option.textContent = t.id;
    option.title = t.name;
    if (t.id === current) option.selected = true;
    select.appendChild(option);
  });

  select.addEventListener('change', e => {
    const version = e.target.value;
    localStorage.setItem('bible-translation', version);
    updateVerseTexts(version);
    updateVerseLinks(version);
  });

  const toggle = document.createElement('button');
  toggle.id = 'red-letters-toggle';
  toggle.title = 'Toggle red letters (words of Jesus)';
  toggle.textContent = 'A';
  if (!redLetters) toggle.classList.add('off');

  toggle.addEventListener('click', () => {
    const enabled = !getRedLetters();
    localStorage.setItem('red-letters', enabled);
    applyRedLetters(enabled);
    toggle.classList.toggle('off', !enabled);
  });

  const wrapper = document.createElement('div');
  wrapper.className = 'md-header__option';
  wrapper.style.cssText = 'display:flex;align-items:center;gap:.25rem;';
  wrapper.appendChild(select);
  wrapper.appendChild(toggle);

  const paletteOption = headerInner.querySelector('.md-header__option');
  if (paletteOption) {
    headerInner.insertBefore(wrapper, paletteOption);
  } else {
    headerInner.appendChild(wrapper);
  }
}

function init() {
  injectSelector();
  applyRedLetters(getRedLetters());
  const version = getCurrentTranslation();
  updateVerseTexts(version);
  updateVerseLinks(version);
}

if (typeof document$ !== 'undefined') {
  document$.subscribe(init);
} else {
  document.addEventListener('DOMContentLoaded', init);
}
