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
