/*
  This file is part of MediaWiki Code2Code Search
  <https://github.com/ftosoni/mediawiki-code2code-search>.
  Copyright (c) 2026 Francesco Tosoni.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
*/

/**
 * MediaWiki Code2Code Search - main.js
 * Vanilla JS implementation for Codex UI
 */

const CONFIG = {
    apiSearch: '/search',
    apiCode: '/code',
    defaultLang: 'en'
};

const EVAL_QUERIES = {
    A1: { code: "def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a", lang: "Python" },
    A2: { code: "function binarySearch(arr, target) {\n    let lo = 0, hi = arr.length - 1;\n    while (lo <= hi) {\n        const mid = (lo + hi) >> 1;\n        if (arr[mid] === target) return mid;\n        if (arr[mid] < target) lo = mid + 1;\n        else hi = mid - 1;\n    }\n    return -1;\n}", lang: "JavaScript" },
    A3: { code: "function truncateString(string $str, int $maxLen,\n                        string $ellipsis = '...'): string {\n    if (mb_strlen($str) <= $maxLen) {\n        return $str;\n    }\n    return mb_substr($str, 0, $maxLen - mb_strlen($ellipsis)) . $ellipsis;\n}", lang: "PHP" },
    A4: { code: "func encodeJSON(v interface{}) ([]byte, error) {\n    data, err := json.Marshal(v)\n    if err != nil {\n        return nil, fmt.Errorf(\"json encode: %w\", err)\n    }\n    return data, nil\n}", lang: "Go" },
    A5: { code: "def retry(func, max_attempts=3, base_delay=1.0):\n    for attempt in range(max_attempts):\n        try:\n            return func()\n        except Exception:\n            if attempt == max_attempts - 1:\n                raise\n            time.sleep(base_delay * (2 ** attempt))", lang: "Python" },
    B1: { code: "public function canUserEdit(User $user, Title $title): bool {\n    return $user->isAllowed('edit')\n        && !$title->isProtected('edit');\n}", lang: "PHP" },
    B2: { code: "function delayExecution(fn, waitMs) {\n    let timer;\n    return function (...args) {\n        clearTimeout(timer);\n        timer = setTimeout(() => fn.apply(this, args), waitMs);\n    };\n}", lang: "JavaScript" },
    B3: { code: "public function invalidateUserSession(User $user): void {\n    $user->setToken();\n    $user->saveSettings();\n    SessionManager::singleton()->invalidateSessionsForUser($user);\n}", lang: "PHP" },
    B4: { code: "def evict_oldest(cache: dict, max_size: int) -> None:\n    while len(cache) > max_size:\n        oldest_key = next(iter(cache))\n        del cache[oldest_key]", lang: "Python" },
    B5: { code: "public function isRateLimited(string $action, UserIdentity $user): bool {\n    $key = $this->makeKey($action, $user->getId());\n    $count = $this->cache->get($key) ?? 0;\n    return $count >= ($this->limits[$action] ?? PHP_INT_MAX);\n}", lang: "PHP" },
    B6: { code: "function toError(value: unknown): Error {\n    if (value instanceof Error) return value;\n    if (typeof value === 'string') return new Error(value);\n    return new Error(JSON.stringify(value));\n}", lang: "TypeScript" },
    B7: { code: "def make_slug(title: str) -> str:\n    slug = title.lower().strip()\n    slug = re.sub(r'[^\\w\\s-]', '', slug)\n    slug = re.sub(r'[\\s_-]+', '-', slug)\n    return slug.strip('-')", lang: "Python" },
    B8: { code: "public function verifyCaptcha(string $token,\n                              string $userAnswer): bool {\n    $expected = $this->store->get($token);\n    if ($expected === null) return false;\n    $this->store->delete($token);\n    return hash_equals($expected, strtolower(trim($userAnswer)));\n}", lang: "PHP" },
    B9: { code: "func processWithPool(jobs []string, workers int,\n                     fn func(string) error) []error {\n    sem := make(chan struct{}, workers)\n    errs := make([]error, len(jobs))\n    var wg sync.WaitGroup\n    for i, job := range jobs {\n        wg.Add(1)\n        sem <- struct{}{}\n        go func(idx int, j string) {\n            defer func() { <-sem; wg.Done() }()\n            errs[idx] = fn(j)\n        }(i, job)\n    }\n    wg.Wait()\n    return errs\n}", lang: "Go" },
    B10: { code: "private function getDescendants(int $catId, int $depth = 0): array {\n    if ($depth > $this->maxDepth) return [];\n    $children = $this->db->selectFieldValues(\n        'categorylinks', 'cl_from',\n        ['cl_to' => $catId, 'cl_type' => 'subcat']\n    );\n    $result = $children;\n    foreach ($children as $child) {\n        $result = array_merge(\n            $result, $this->getDescendants($child, $depth + 1)\n        );\n    }\n    return $result;\n}", lang: "PHP" },
    B11: { code: "def fetch_all_pages(endpoint, params, page_size=50):\n    results, offset = [], 0\n    while True:\n        params.update({'limit': page_size, 'offset': offset})\n        batch = requests.get(endpoint, params=params).json()\n        if not batch:\n            break\n        results.extend(batch)\n        offset += page_size\n    return results", lang: "Python" },
    B12: { code: "func doWithRetry(client *http.Client, req *http.Request,\n                 maxRetries int) (*http.Response, error) {\n    var lastErr error\n    for i := 0; i < maxRetries; i++ {\n        resp, err := client.Do(req)\n        if err == nil && resp.StatusCode < 500 {\n            return resp, nil\n        }\n        lastErr = err\n        time.Sleep(time.Duration(i+1) * time.Second)\n    }\n    return nil, lastErr\n}", lang: "Go" },
    C1: { code: "function computeFileHash(string $filepath): string {\n    return hash_file('sha256', $filepath);\n}", lang: "PHP" },
    C2: { code: "def parse_iso_date(date_str: str) -> datetime:\n    return datetime.fromisoformat(\n        date_str.replace('Z', '+00:00')\n    )", lang: "Python" },
    C3: { code: "func fanOut(inputs []string,\n            process func(string) (string, error)) ([]string, error) {\n    results := make([]string, len(inputs))\n    var wg sync.WaitGroup\n    errCh := make(chan error, len(inputs))\n    for i, inp := range inputs {\n        wg.Add(1)\n        go func(idx int, s string) {\n            defer wg.Done()\n            r, err := process(s)\n            if err != nil { errCh <- err; return }\n            results[idx] = r\n        }(i, inp)\n    }\n    wg.Wait()\n    close(errCh)\n    if err := <-errCh; err != nil { return nil, err }\n    return results, nil\n}", lang: "Go" },
    C4: { code: "function throttle<T extends (...args: unknown[]) => void>(\n    fn: T, limitMs: number\n): T {\n    let lastCall = 0;\n    return function (...args) {\n        const now = Date.now();\n        if (now - lastCall >= limitMs) {\n            lastCall = now;\n            fn(...args);\n        }\n    } as T;\n}", lang: "TypeScript" },
    C5: { code: "-- Lua\nlocal function serialize(val, indent)\n    indent = indent or 0\n    if type(val) == \"table\" then\n        local parts = {}\n        for k, v in pairs(val) do\n            parts[#parts+1] = string.rep(\"  \", indent+1)\n                .. tostring(k) .. \" = \" .. serialize(v, indent+1)\n        end\n        return \"{\\n\" .. table.concat(parts, \",\\n\")\n            .. \"\\n\" .. string.rep(\"  \", indent) .. \"}\"\n    end\n    return tostring(val)\nend", lang: "Lua" },
    C6: { code: "def run_sparql(query: str,\n               endpoint: str = 'https://query.wikidata.org/sparql'\n              ) -> list:\n    resp = requests.get(\n        endpoint,\n        params={'query': query, 'format': 'json'},\n        headers={'User-Agent': 'EvalBot/1.0'}\n    )\n    resp.raise_for_status()\n    return resp.json()['results']['bindings']", lang: "Python" },
    D1: { code: "public function extractWikiLinks(string $wikitext): array {\n    $links = [];\n    if (preg_match_all(\n            '/\\[\\[([^|\\]]+)(?:\\|[^\\]]+)?\\]\\]/', $wikitext, $m)) {\n        foreach ($m[1] as $target) {\n            $links[] = Title::newFromText(trim($target));\n        }\n    }\n    return array_filter($links);\n}", lang: "PHP" },
    D2: { code: "def compute_swhid(content: bytes) -> str:\n    sha1 = hashlib.new('sha1')\n    header = f\"blob {len(content)}\\0\".encode()\n    sha1.update(header + content)\n    return f\"swh:1:cnt:{sha1.hexdigest()}\"", lang: "Python" },
    D3: { code: "def parse_irc_message(raw: str) -> dict:\n    prefix, command, params = None, None, []\n    if raw.startswith(':'):\n        prefix, raw = raw[1:].split(' ', 1)\n    parts = raw.split(' ', 1)\n    command = parts[0]\n    if len(parts) > 1:\n        ti = parts[1].find(' :')\n        if ti >= 0:\n            params = parts[1][:ti].split()\n            params.append(parts[1][ti+2:])\n        else:\n            params = parts[1].split()\n    return {'prefix': prefix, 'command': command, 'params': params}", lang: "Python" },
    D4: { code: "public function run(string $hook, array $args = []): bool {\n    foreach ($this->getHandlers($hook) as $handler) {\n        $ret = $handler(...$args);\n        if ($ret === false) {\n            return false;\n        }\n    }\n    return true;\n}", lang: "PHP" },
    D5: { code: "func (f *BloomFilter) Contains(item []byte) bool {\n    for _, h := range f.hashFunctions(item) {\n        idx := h % uint64(len(f.bits))\n        if f.bits[idx/8]&(1<<(idx%8)) == 0 {\n            return false\n        }\n    }\n    return true\n}", lang: "Go" }
};

let currentLang = localStorage.getItem('code2code_lang') || CONFIG.defaultLang;
let i18nData = {};
let activeFilters = {
    repos: ['all'],
    langs: ['all'],
    types: ['all']
};
let lastSearchResults = [];

// --- Initialization ---

document.addEventListener('DOMContentLoaded', async () => {
    // Initial language setup
    await loadLanguage(currentLang);
    document.getElementById('lang-select').value = currentLang;

    // Event Listeners
    setupEventListeners();
});

function setupEventListeners() {
    // Language selector
    document.getElementById('lang-select').addEventListener('change', (e) => {
        changeLanguage(e.target.value);
    });

    // Search button
    document.getElementById('btn-search').addEventListener('click', performSearch);

    // Filter chips
    setupFilterChips('filter-repos', 'repos');
    setupFilterChips('filter-langs', 'langs');
    setupFilterChips('filter-types', 'types');

    // Enter key in textarea (Cmd/Ctrl + Enter to search)
    document.getElementById('search-query').addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            performSearch();
        }
    });

    // Examples selector
    document.getElementById('example-queries').addEventListener('change', (e) => {
        const qid = e.target.value;
        if (qid && EVAL_QUERIES[qid]) {
            const queryData = EVAL_QUERIES[qid];
            document.getElementById('search-query').value = queryData.code;

            // Update language filter chip to match query language
            const lang = queryData.lang;
            const langContainer = document.getElementById('filter-langs');
            const chips = langContainer.querySelectorAll('.cdx-button');
            chips.forEach(c => c.classList.remove('active'));

            const supportedLangs = ['Python', 'C++', 'C', 'PHP', 'JavaScript', 'TypeScript', 'Lua', 'Go', 'Java', 'Rust', 'Ruby', 'Perl'];
            if (supportedLangs.includes(lang)) {
                const targetChip = langContainer.querySelector(`[data-value="${lang}"]`);
                if (targetChip) {
                    targetChip.classList.add('active');
                    activeFilters.langs = [lang];
                }
            } else {
                const allChip = langContainer.querySelector(`[data-value="all"]`);
                if (allChip) {
                    allChip.classList.add('active');
                    activeFilters.langs = ['all'];
                }
            }
            updateTemplateStatus();
        }
    });

    // Initial constraints
    updateTemplateStatus();
}

function setupFilterChips(containerId, filterKey) {
    const container = document.getElementById(containerId);
    const chips = container.querySelectorAll('.cdx-button');
    const allChip = container.querySelector('[data-value="all"]');

    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            const val = chip.getAttribute('data-value');

            if (val === 'all') {
                // If "All" is clicked, it becomes active and everything else is deselected
                chips.forEach(c => c.classList.remove('active'));
                allChip.classList.add('active');
                activeFilters[filterKey] = ['all'];
            } else {
                // Multi-select toggle
                if (chip.classList.contains('active')) {
                    // Toggle OFF
                    const remaining = activeFilters[filterKey].filter(v => v !== val && v !== 'all');
                    if (remaining.length === 0) {
                        // Revert to "All"
                        chips.forEach(c => c.classList.remove('active'));
                        allChip.classList.add('active');
                        activeFilters[filterKey] = ['all'];
                    } else {
                        chip.classList.remove('active');
                        activeFilters[filterKey] = remaining;
                    }
                } else {
                    // Toggle ON
                    chip.classList.add('active');
                    // Remove "All" if it was active
                    if (allChip.classList.contains('active')) {
                        allChip.classList.remove('active');
                        activeFilters[filterKey] = [val];
                    } else {
                        activeFilters[filterKey].push(val);
                    }
                }
            }

            // Cross-filter logic
            if (filterKey === 'langs') {
                updateTemplateStatus();
            }
        });
    });
}

function updateTemplateStatus() {
    const isCppSelected = activeFilters.langs.includes('C++') || activeFilters.langs.includes('all');
    const templateChip = document.querySelector('#filter-types [data-value="template"]');
    if (!templateChip) return;

    if (isCppSelected) {
        templateChip.disabled = false;
        templateChip.classList.remove('disabled');
    } else {
        templateChip.disabled = true;
        templateChip.classList.add('disabled');
        if (templateChip.classList.contains('active')) {
            templateChip.classList.remove('active');
            activeFilters.types = activeFilters.types.filter(v => v !== 'template');
            // If types empty, select "all"
            if (activeFilters.types.length === 0) {
                const allTypesChip = document.querySelector('#filter-types [data-value="all"]');
                if (allTypesChip) allTypesChip.classList.add('active');
                activeFilters.types = ['all'];
            }
        }
    }
}

// --- I18n Logic ---

async function loadLanguage(lang) {
    try {
        const response = await fetch(`i18n/${lang}.json`);
        i18nData = await response.json();
        applyI18n();
        currentLang = lang;
        localStorage.setItem('code2code_lang', lang);
        document.documentElement.lang = lang;
    } catch (error) {
        console.error('Failed to load language:', lang, error);
    }
}

function applyI18n() {
    // Header & Hero
    document.querySelector('.app-header__title').textContent = i18nData.main_title || 'Code2Code Search';
    document.querySelector('.page-hero__heading').textContent = i18nData.search_title || 'Search source code';
    document.querySelector('.page-hero__desc').textContent = i18nData.subtitle || 'Semantic Neural Retrieval Engine';

    // Form
    document.querySelector('label[for="search-query"]').textContent = i18nData.search_label || 'Code snippet';
    document.getElementById('search-query').placeholder = i18nData.placeholder || 'def gcd(a,b) : ...';
    document.getElementById('btn-search').textContent = i18nData.btn_search || 'Search code';

    document.querySelector('label[for="example-queries"]').textContent = i18nData.example_queries_label || 'Try an evaluation query example';
    document.getElementById('example-queries').options[0].textContent = i18nData.example_queries_placeholder || '-- Select an evaluation query --';

    // Filters Labels
    document.querySelector('#filter-repos .filter-label').textContent = i18nData.group_label || 'Repository groups';
    document.querySelector('#filter-langs .filter-label').textContent = i18nData.lang_label || 'Languages';
    document.querySelector('#filter-types .filter-label').textContent = i18nData.type_label || 'Result type';

    // Filter values (Groups)
    updateChipText('#filter-repos', 'all', i18nData.group_all || 'All');
    updateChipText('#filter-repos', 'core', i18nData.group_core || 'Core');
    updateChipText('#filter-repos', 'things', i18nData.group_things || 'Things');
    updateChipText('#filter-repos', 'libraries', i18nData.group_libraries || 'Libraries');
    updateChipText('#filter-repos', 'deployed', i18nData.group_deployed || 'Deployed');
    updateChipText('#filter-repos', 'operations', i18nData.group_operations || 'Operations');
    updateChipText('#filter-repos', 'puppet', i18nData.group_puppet || 'Puppet');
    updateChipText('#filter-repos', 'pywikibot', i18nData.group_pywikibot || 'Pywikibot');
    updateChipText('#filter-repos', 'devtools', i18nData.group_devtools || 'Devtools');
    updateChipText('#filter-repos', 'analytics', i18nData.group_analytics || 'Analytics');
    updateChipText('#filter-repos', 'wmcs', i18nData.group_wmcs || 'WMCS');
    updateChipText('#filter-repos', 'apps', i18nData.group_apps || 'Apps');

    // Types
    updateChipText('#filter-types', 'all', i18nData.type_all || 'All');
    updateChipText('#filter-types', 'function', i18nData.type_function || 'Function');
    updateChipText('#filter-types', 'type', i18nData.type_type || 'Type');
    updateChipText('#filter-types', 'template', i18nData.type_template || 'Template');

    // Summary
    const matchesFoundEl = document.getElementById('matches-found-label');
    if (matchesFoundEl) matchesFoundEl.textContent = i18nData.matches_found || 'Matches found';

    const loadingTextEl = document.getElementById('loading-text');
    if (loadingTextEl) loadingTextEl.textContent = i18nData.loading_message || 'Searching for code matches... Please wait.';

    // Footer
    const footerDev = document.getElementById('footer-dev');
    if (footerDev) {
        footerDev.innerHTML = `${i18nData.created_by || 'Developed by:'}&nbsp;<a href="https://meta.wikimedia.org/wiki/Special:MyLanguage/User:Super_nabla" target="_blank">Super nabla 🪰</a>&nbsp;(<a href="https://meta.wikimedia.org/wiki/Special:MyLanguage/Indic_MediaWiki_Developers_User_Group" target="_blank">${i18nData.indic_ug || 'Indic MediaWiki Developers UG'}</a>)`;
    }

    const footerLicence = document.getElementById('footer-licence');
    if (footerLicence) {
        footerLicence.innerHTML = `${i18nData.licence || 'Licence:'} <a href="https://github.com/ftosoni/mediawiki-code2code-search/blob/main/LICENSE.md" target="_blank">Apache-2.0</a>`;
    }

    const footerDocs = document.getElementById('footer-docs');
    if (footerDocs) {
        footerDocs.innerHTML = `${i18nData.documentation_prefix || 'Documentation:'}&nbsp;<a href="https://www.mediawiki.org/wiki/Special:MyLanguage/Code2Code_Search" target="_blank">MediaWiki</a>&nbsp;·&nbsp;<a href="/docs" target="_blank">${i18nData.docs || 'API'}</a>`;
    }

    const footerPresentation = document.getElementById('footer-presentation');
    if (footerPresentation) footerPresentation.textContent = i18nData.presentation || 'Presentation';

    const footerWikidata = document.getElementById('footer-wikidata');
    if (footerWikidata) footerWikidata.textContent = i18nData.wikidata || 'Wikidata Q-item';

    const footerToolhub = document.getElementById('footer-toolhub');
    if (footerToolhub) footerToolhub.textContent = i18nData.toolhub || 'Toolhub';

    const footerSource = document.getElementById('footer-source');
    if (footerSource) {
        footerSource.innerHTML = `${i18nData.source || 'Source'}:&nbsp;<a href="https://github.com/ftosoni/mediawiki-code2code-search" target="_blank">GitHub</a>&nbsp;·&nbsp;<a href="https://archive.softwareheritage.org/browse/origin/directory/?origin_url=https://github.com/ftosoni/mediawiki-code2code-search" target="_blank">SWH</a>`;
    }

    const footerIssues = document.getElementById('footer-issues');
    if (footerIssues) footerIssues.textContent = i18nData.issues || 'Report an issue';

    const footerGrant = document.getElementById('footer-grant');
    if (footerGrant) footerGrant.innerHTML = i18nData.sloan_grant || 'Supported by the Alfred P. Sloan Foundation';

    const footerQwen = document.getElementById('footer-qwen');
    if (footerQwen) footerQwen.innerHTML = i18nData.powered_by_qwen || 'Powered by <a href="https://huggingface.co/Qwen/Qwen3-Embedding-0.6B" target="_blank">Qwen</a>';

    const footerSwhArchive = document.getElementById('footer-swh-archive');
    if (footerSwhArchive) footerSwhArchive.innerHTML = i18nData.data_archived_by_swh || 'Data archived by <a href="https://www.softwareheritage.org/" target="_blank">Software Heritage</a>';

    const footerTitleCredits = document.getElementById('footer-title-credits');
    if (footerTitleCredits) footerTitleCredits.textContent = i18nData.footer_section_credits || 'Credits & Project';

    const footerTitleResources = document.getElementById('footer-title-resources');
    if (footerTitleResources) footerTitleResources.textContent = i18nData.footer_section_resources || 'Resources';

    const footerTitleSource = document.getElementById('footer-title-source');
    if (footerTitleSource) footerTitleSource.textContent = i18nData.footer_section_source || 'Source & Support';

    const footerTitleStatus = document.getElementById('footer-title-status');
    if (footerTitleStatus) footerTitleStatus.textContent = i18nData.footer_section_status || 'Licence & Status';

    const footerReleaseDateLabel = document.getElementById('footer-release-date-label');
    if (footerReleaseDateLabel) footerReleaseDateLabel.textContent = i18nData.footer_release_date || 'Release date:';

    // Re-render results if any
    if (lastSearchResults.length > 0) {
        displayResults({ results: lastSearchResults });
    }
}

function updateChipText(parentSelector, dataValue, text) {
    const chip = document.querySelector(`${parentSelector} [data-value="${dataValue}"]`);
    if (chip) chip.textContent = text;
}

async function changeLanguage(lang) {
    await loadLanguage(lang);
}

// --- Search Logic ---

async function performSearch() {
    const query = document.getElementById('search-query').value.trim();
    if (!query) return;

    // UI State
    const searchBtn = document.getElementById('btn-search');
    const loadingArea = document.getElementById('loading-area');
    const resultsArea = document.getElementById('results-area');
    const resultsList = document.getElementById('results-list');

    searchBtn.disabled = true;
    searchBtn.textContent = i18nData.btn_loading || 'Searching...';
    loadingArea.style.display = 'flex';
    resultsArea.style.display = 'none';
    resultsList.innerHTML = '';

    try {
        const payload = {
            query: query,
            repo_group: activeFilters.repos,
            language_filter: activeFilters.langs,
            type_filter: activeFilters.types,
            top_k: 10
        };

        const response = await fetch(CONFIG.apiSearch, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Search failed');

        const resultsData = await response.json();
        displayResults(resultsData);
    } catch (error) {
        console.error('Search error:', error);
        resultsList.innerHTML = `<div class="cdx-message cdx-message--error">${error.message}</div>`;
        resultsArea.style.display = 'block';
    } finally {
        searchBtn.disabled = false;
        searchBtn.textContent = i18nData.btn_search || 'Search code';
        loadingArea.style.display = 'none';
    }
}

function displayResults(data) {
    const resultsArea = document.getElementById('results-area');
    const resultsList = document.getElementById('results-list');
    const countDisplay = document.getElementById('count-results');

    const results = data.results || [];
    lastSearchResults = results;
    countDisplay.textContent = results.length;
    resultsArea.style.display = 'block';
    resultsList.innerHTML = '';

    if (results.length === 0) {
        resultsList.innerHTML = `<p class="no-results">${i18nData.no_results || 'No results found.'}</p>`;
        return;
    }

    results.forEach((item, index) => {
        const card = createResultCard(item, index);
        resultsList.appendChild(card);
    });
}

function createResultCard(item, index) {
    const card = document.createElement('div');
    card.className = 'result-card';
    card.setAttribute('data-swhid', item.swhid);

    const typeClass = `type-${item.type.toLowerCase()}`;
    const typeLabel = i18nData[`type_${item.type.toLowerCase()}`] || item.type;
    const repoGroupLabel = i18nData[`group_${item.repo_group.toLowerCase()}`] || item.repo_group;

    card.innerHTML = `
        <div class="result-header">
            <div class="result-main-info">
                <span class="result-repo-tag">${repoGroupLabel}</span>
                <span class="result-repo-name">${item.repo_name}</span>
                <h2 class="result-filename">${item.filepath.split('/').pop()}</h2>
                <div class="result-path">${item.filepath}</div>
            </div>
            <div class="result-score">
                <span class="score-label">${i18nData.recall_score || 'Score'}</span>
                <span class="score-value">${(item.recall_score * 100).toFixed(1)}%</span>
            </div>
        </div>
        <div class="result-body">
            <div class="result-type-badge ${typeClass}">${typeLabel}</div>
            <div class="result-name">${item.name}</div>
            <a href="https://archive.softwareheritage.org/${item.swhid}" target="_blank" class="swhid-link" title="View on Software Heritage">
                SWHID: ${item.swhid}
            </a>
            
            <div class="code-wrapper collapsed" id="code-wrapper-${index}">
                <pre><code>${item.highlighted_code || escapeHtml(item.code || '')}</code></pre>
                <div class="code-gradient"></div>
            </div>
            <button class="expand-btn" id="expand-btn-${index}">${i18nData.show_more || 'Show more'}</button>
        </div>
    `;

    // Expansion logic
    const expandBtn = card.querySelector('.expand-btn');
    const codeWrapper = card.querySelector('.code-wrapper');

    expandBtn.addEventListener('click', () => {
        if (codeWrapper.classList.contains('collapsed')) {
            codeWrapper.classList.remove('collapsed');
            expandBtn.textContent = i18nData.show_less || 'Collapse';
        } else {
            codeWrapper.classList.add('collapsed');
            expandBtn.textContent = i18nData.show_more || 'Show more';
        }
    });

    // Only show expand button if code is actually overflowing
    // We need to wait a bit for the layout to settle or use requestAnimationFrame
    requestAnimationFrame(() => {
        const pre = codeWrapper.querySelector('pre');
        if (pre.scrollHeight <= 500) { // 500 is the max-height from CSS
            expandBtn.style.display = 'none';
            codeWrapper.classList.remove('collapsed');
        }
    });

    return card;
}


function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
