const TRANSLATIONS = [
  { id: 'CJB', name: 'Complete Jewish Bible' },
  { id: 'ESV', name: 'English Standard Version' },
  { id: 'NIV', name: 'New International Version' },
  { id: 'NKJV', name: 'New King James Version' },
  { id: 'NLT', name: 'New Living Translation' },
];

function getCurrentTranslation() {
  return localStorage.getItem('bible-translation') || 'NIV';
}

function setVerseText(el, text) {
  const paragraphs = text.split('\n\n');
  if (paragraphs.length <= 1) {
    el.textContent = text;
    return;
  }
  // Safely escape each paragraph then join with <br><br>
  const parts = paragraphs.map(p => {
    const tmp = document.createElement('span');
    tmp.textContent = p;
    return tmp.innerHTML;
  });
  el.innerHTML = parts.join('<br><br>');
}

function updateVerseTexts(version) {
  document.querySelectorAll('.verse-text').forEach(el => {
    const text = el.dataset[version.toLowerCase()];
    if (text) setVerseText(el, text);
  });
}

function injectSelector() {
  if (document.getElementById('translation-select')) return;

  const headerInner = document.querySelector('.md-header__inner');
  if (!headerInner) return;

  const current = getCurrentTranslation();

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
  });

  const wrapper = document.createElement('div');
  wrapper.className = 'md-header__option';
  wrapper.style.cssText = 'display:flex;align-items:center;';
  wrapper.appendChild(select);

  const paletteOption = headerInner.querySelector('.md-header__option');
  if (paletteOption) {
    headerInner.insertBefore(wrapper, paletteOption);
  } else {
    headerInner.appendChild(wrapper);
  }
}

function init() {
  injectSelector();
  updateVerseTexts(getCurrentTranslation());
}

if (typeof document$ !== 'undefined') {
  document$.subscribe(init);
} else {
  document.addEventListener('DOMContentLoaded', init);
}
