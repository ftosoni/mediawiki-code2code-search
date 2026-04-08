const { useState, useEffect, useRef } = React;

// --- Three.js Background Component ---
const BackgroundVortex = ({ speedMultiplier }) => {
    const speedRef = useRef(1);

    useEffect(() => {
        speedRef.current = speedMultiplier;
    }, [speedMultiplier]);

    useEffect(() => {
        const container = document.getElementById('canvas-container');
        if (!container) return;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        container.appendChild(renderer.domElement);

        // Lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        scene.add(ambientLight);

        const pointLight = new THREE.PointLight(0x8da2fb, 2, 20); // Cool blue light
        scene.add(pointLight);

        // Particles
        const particlesCount = 1800;
        const particleGroup = new THREE.Group();

        // Octahedron geometry for diamond shape
        const geometry = new THREE.OctahedronGeometry(0.07, 0);

        for (let i = 0; i < particlesCount; i++) {
            const color = new THREE.Color();
            if (Math.random() > 0.5) {
                color.setHex(0xff8c00); // Saffron
            } else {
                color.setHex(0x4b61d1); // Savoy Blue
            }

            const material = new THREE.MeshPhongMaterial({
                color: color,
                transparent: true,
                opacity: Math.random() * 0.4 + 0.2,
                shininess: 100,
                specular: 0xffffff
            });

            const mesh = new THREE.Mesh(geometry, material);

            // Spiral/Vortex distribution
            const radius = (Math.random() * 8) + 1;
            const theta = Math.random() * Math.PI * 2;
            const y = (Math.random() - 0.5) * 15;

            mesh.position.set(
                radius * Math.cos(theta),
                y,
                radius * Math.sin(theta)
            );

            mesh.rotation.x = Math.random() * Math.PI;
            mesh.rotation.y = Math.random() * Math.PI;

            const s = Math.random() * 0.7 + 0.3;
            mesh.scale.set(s, s, s);

            particleGroup.add(mesh);
        }

        scene.add(particleGroup);
        camera.position.z = 7;

        let mouseX = 0, mouseY = 0;
        const handleMouseMove = (e) => {
            mouseX = (e.clientX - window.innerWidth / 2) / 100;
            mouseY = (e.clientY - window.innerHeight / 2) / 100;
        };
        window.addEventListener('mousemove', handleMouseMove);

        let currentAnimSpeed = 0.0015;

        const animate = () => {
            requestAnimationFrame(animate);

            const targetAnimSpeed = speedRef.current > 1 ? 0.025 : 0.0015;
            currentAnimSpeed += (targetAnimSpeed - currentAnimSpeed) * 0.05;

            particleGroup.rotation.y += currentAnimSpeed;
            particleGroup.rotation.x += currentAnimSpeed * 0.3;

            // Shiny glint tracking
            pointLight.position.x = mouseX * 5;
            pointLight.position.y = -mouseY * 5;
            pointLight.position.z = 5;

            const time = Date.now() * 0.001;

            particleGroup.children.forEach((p, idx) => {
                p.rotation.y += 0.015;
                // Twinkle effect (selective)
                if (idx % 15 === 0) {
                    p.material.opacity = (Math.sin(time * 2 + idx) * 0.15) + 0.35;
                }
            });

            camera.position.x += (mouseX - camera.position.x) * 0.04;
            camera.position.y += (-mouseY - camera.position.y) * 0.04;
            camera.lookAt(scene.position);

            renderer.render(scene, camera);
        };

        animate();

        const handleResize = () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('resize', handleResize);
            if (container.contains(renderer.domElement)) {
                container.removeChild(renderer.domElement);
            }
        };
    }, []); // Only run once

    return null;
};

// --- Individual Result Item Component ---
const ResultItem = ({ res, i, t }) => {
    const [expanded, setExpanded] = useState(false);
    const [code, setCode] = useState("");
    const [codeLoading, setCodeLoading] = useState(true);
    const [codeError, setCodeError] = useState(false);
    const codeRef = useRef(null);
    const [isLong, setIsLong] = useState(false);

    useEffect(() => {
        const fetchCode = async () => {
            if (res.code) {
                setCode(res.code);
                setCodeLoading(false);
                return;
            }
            setCodeLoading(true);
            try {
                const response = await fetch(`/code?swhid=${encodeURIComponent(res.swhid)}`);
                const data = await response.json();
                if (data.code) {
                    setCode(data.code);
                } else {
                    setCodeError(true);
                }
            } catch (error) {
                console.error("Failed to fetch code:", error);
                setCodeError(true);
            } finally {
                setCodeLoading(false);
            }
        };
        fetchCode();
    }, [res.swhid, res.code]);

    useEffect(() => {
        if (code && codeRef.current && codeRef.current.scrollHeight > 300) {
            setIsLong(true);
        }
    }, [code]);

    return (
        <div className="result-card" style={{ animationDelay: `${i * 0.15}s` }}>
            <div className="result-header">
                <div className="file-info" style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                <span style={{
                                    fontSize: '0.65rem',
                                    color: '#8da2fb',
                                    fontWeight: 700,
                                    background: 'rgba(141, 162, 251, 0.1)',
                                    padding: '2px 8px',
                                    borderRadius: '4px',
                                    textTransform: 'uppercase',
                                    letterSpacing: '1px'
                                }}>
                                    {t(`group_${res.repo_group}`) || res.repo_group}
                                </span>
                                <span style={{ color: '#aaa', fontSize: '0.8rem' }}>{res.repo_name}</span>
                            </div>
                            <h3>{(res.filepath || "").split('/').pop()}</h3>
                            <div style={{ color: '#666', fontSize: '0.75rem' }}>{(res.filepath || "").split('/').slice(0, -1).join('/')}</div>
                        </div>
                        <div style={{
                            padding: '4px 10px',
                            borderRadius: '8px',
                            fontSize: '0.7rem',
                            fontWeight: 'bold',
                            textTransform: 'uppercase',
                            letterSpacing: '1px',
                            background: (res.type.includes('type')) ? 'rgba(157, 0, 255, 0.2)' : 'rgba(0, 255, 127, 0.1)',
                            color: (res.type.includes('type')) ? '#E1B0FF' : '#00FF7F',
                            border: `1px solid ${(res.type.includes('type')) ? 'rgba(157, 0, 255, 0.3)' : 'rgba(0, 255, 127, 0.2)'}`
                        }}>
                            {t(`type_${res.type}`) || res.type.replace('_', ' ')}
                        </div>
                    </div>
                    <div style={{ color: 'var(--accent-india)', fontWeight: 700, fontSize: '1.1rem', wordBreak: 'break-all' }}>{res.name}</div>
                    <a
                        href={`https://archive.softwareheritage.org/${res.swhid}`}
                        target="_blank"
                        className="swhid-link"
                        title="SWHID Copy to Clipboard"
                    >
                        {res.swhid}
                    </a>
                </div>
                <div className="score-box" style={{ flexShrink: 0 }}>
                    <div className="score-label" style={{ color: '#FF9933', opacity: 0.8, fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '1px' }}>{t('recall_score')}</div>
                    <div className="score-value rank" style={{ color: '#FF9933', fontSize: '1.2rem', fontWeight: 800 }}>{(res.recall_score || 0).toFixed(4)}</div>
                </div>
            </div>

            <div className={`code-wrapper ${isLong && !expanded ? 'collapsed' : ''}`} ref={codeRef}>
                {codeLoading ? (
                    <div style={{ padding: '2rem', textAlign: 'center', opacity: 0.5 }}>
                        <div className="loader" style={{ width: '24px', height: '24px', margin: '0 auto 10px' }}></div>
                        <span style={{ fontSize: '0.8rem' }}>{t('fetching_code')}</span>
                    </div>
                ) : codeError ? (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#ff6b6b', fontSize: '0.8rem' }}>
                        ⚠️ {t('error_fetching_code')}
                    </div>
                ) : (
                    <pre><code>{code}</code></pre>
                )}
                {isLong && !expanded && <div className="code-gradient"></div>}
            </div>

            {isLong && (
                <button className="expand-btn" onClick={() => setExpanded(!expanded)}>
                    <span>{expanded ? '▲' : '▼'}</span>
                    {expanded ? t('show_less') : t('show_more')}
                </button>
            )}
        </div>
    );
};

// --- Main React Application ---
const App = () => {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [typeFilter, setTypeFilter] = useState("all");
    const [repoGroups, setRepoGroups] = useState(["all"]);
    const [langFilters, setLangFilters] = useState(["all"]);
    const [loading, setLoading] = useState(false);
    const [speed, setSpeed] = useState(1);
    const [currentLang, setCurrentLang] = useState("en");
    const [translations, setTranslations] = useState(null);
    const [translating, setTranslating] = useState(true);

    // Fetch translations from JSON
    useEffect(() => {
        const loadTranslations = async () => {
            setTranslating(true);
            try {
                const response = await fetch(`/i18n/${currentLang}.json`);
                const data = await response.json();
                setTranslations(data);
            } catch (error) {
                console.error("Failed to load translations:", error);
                // Fallback to English if not already English
                if (currentLang !== 'en') {
                    setCurrentLang('en');
                }
            } finally {
                setTranslating(false);
            }
        };
        loadTranslations();
    }, [currentLang]);

    const t = (key) => translations ? (translations[key] || key) : "...";

    const toggleFilter = (item, currentList, setList) => {
        if (item === 'all') {
            setList(['all']);
            return;
        }

        let newList = [...currentList];
        // If 'all' is present, remove it when adding a specific filter
        if (newList.includes('all')) {
            newList = [item];
        } else {
            if (newList.includes(item)) {
                newList = newList.filter(i => i !== item);
            } else {
                newList.push(item);
            }
        }

        // If nothing left, default back to 'all'
        if (newList.length === 0) {
            newList = ['all'];
        }
        setList(newList);
    };

    const handleSearch = async () => {
        if (!query.trim()) return;
        setLoading(true);
        setSpeed(10);
        setResults([]);

        try {
            const response = await fetch("/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query,
                    top_k: 10,
                    type_filter: typeFilter,
                    repo_group: repoGroups,
                    language_filter: langFilters
                })
            });
            const data = await response.json();
            setResults(data.results || []);
        } catch (error) {
            console.error("Search failed:", error);
        } finally {
            setLoading(false);
            setTimeout(() => setSpeed(1), 2000);
        }
    };


    return (
        <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <BackgroundVortex speedMultiplier={speed} />

            {translating && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    background: 'rgba(5,5,5,0.8)',
                    backdropFilter: 'blur(10px)',
                    zIndex: 9999,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    animation: 'fadeIn 0.3s ease'
                }}>
                    <div className="loader"></div>
                </div>
            )}

            <div className="lang-selector">
                <span style={{ fontSize: '0.8rem', opacity: 0.5 }}>🌐</span>
                <select value={currentLang} onChange={(e) => setCurrentLang(e.target.value)}>
                    <option value="as">অসমীয়া (AS)</option>
                    <option value="bn">বাংলা (BN)</option>
                    <option value="en">English (EN)</option>
                    <option value="fr">Français (FR)</option>
                    <option value="gu">ગુજરાતી (GU)</option>
                    <option value="hi">हिन्दी (HI)</option>
                    <option value="it">Italiano (IT)</option>
                    <option value="kn">ಕನ್ನಡ (KN)</option>
                    <option value="mai">मैथिली (MAI)</option>
                    <option value="ml">മലയാളം (ML)</option>
                    <option value="mr">मराठी (MR)</option>
                    <option value="or">ଓଡ଼ିଆ (OR)</option>
                    <option value="pa">ਪੰਜਾਬੀ (PA)</option>
                    <option value="sat">ᱥᱟᱱᱛᱟᱲᱤ (SAT)</option>
                    <option value="ta">தமிழ் (TA)</option>
                    <option value="te">తెలుగు (TE)</option>
                    <option value="ur">اردو (UR)</option>
                </select>
            </div>

            <div className="header">
                <p>{t('search_title')}</p>
                <h1>{t('main_title')}</h1>
                <p style={{ fontSize: '0.65rem', opacity: 0.4, letterSpacing: '6px', marginTop: '10px' }}>{t('subtitle')}</p>
            </div>

            <div className="group-selector">
                {['all', 'core', 'things', 'libraries', 'deployed', 'operations', 'puppet', 'pywikibot', 'devtools', 'analytics', 'wmcs', 'apps'].map(g => (
                    <div
                        key={g}
                        className={`group-chip ${repoGroups.includes(g) ? 'active' : ''} ${g === 'all' ? 'all-chip' : ''}`}
                        onClick={() => toggleFilter(g, repoGroups, setRepoGroups)}
                    >
                        {t(`group_${g}`)}
                    </div>
                ))}
            </div>

            <div className="group-selector" style={{ marginTop: '-1rem', paddingBottom: '2.5rem', gap: '6px' }}>
                {['all', 'Python', 'C++', 'C', 'PHP', 'JavaScript', 'TypeScript', 'Lua', 'Go', 'Java', 'Rust'].map(l => (
                    <div
                        key={l}
                        className={`lang-chip ${langFilters.includes(l) ? 'active' : ''} ${l === 'all' ? 'all-chip' : ''}`}
                        onClick={() => toggleFilter(l, langFilters, setLangFilters)}
                    >
                        {l === 'all' ? t('group_all') : l}
                    </div>
                ))}
            </div>

            <div className="search-container">
                <textarea
                    placeholder={`${t('placeholder')}\n\ndef greatest_common_divisor(m,n) :\n  if (n==0) :\n    return m\n  return greatest_common_divisor(n,m%n)`}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    disabled={loading}
                />
                <div className="type-selector">
                    {['all', 'function', 'type', 'template_function', 'template_type'].map(f => (
                        <div
                            key={f}
                            className={`type-chip ${typeFilter === f ? 'active' : ''}`}
                            onClick={() => setTypeFilter(f)}
                        >
                            {t(`type_${f}`)}
                        </div>
                    ))}
                </div>
                <div className="search-footer">
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    </div>
                    <button className="search-btn" onClick={handleSearch} disabled={loading}>
                        {loading ? t('btn_loading') : t('btn_search')}
                    </button>
                </div>
            </div>

            {loading && <div style={{ marginTop: '6rem' }}><div className="loader"></div></div>}

            <div className="results">
                {!loading && results.map((res, i) => (
                    <ResultItem key={i} res={res} i={i} t={t} />
                ))}
                {!loading && query && results.length === 0 && (
                    <div style={{ textAlign: 'center', opacity: 0.3, marginTop: '5rem', fontSize: '1.2rem', fontWeight: 300 }}>{t('no_results')}</div>
                )}
            </div>

            <footer style={{
                marginTop: 'auto',
                padding: '4rem 2rem 2rem 2rem',
                width: '100%',
                maxWidth: '900px',
                textAlign: 'center',
                fontSize: '0.8rem',
                color: '#666',
                borderTop: '1px solid rgba(255,255,255,0.05)',
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                gap: '1rem',
                alignItems: 'center'
            }}>
                <span>
                    {t('created_by')} <a href="https://meta.wikimedia.org/wiki/Special:MyLanguage/User:Super_nabla" target="_blank" style={{ color: 'var(--accent-italy)', textDecoration: 'none' }}>Super nabla 🪰</a> (<a href="https://meta.wikimedia.org/wiki/Special:MyLanguage/Indic_MediaWiki_Developers_User_Group" target="_blank" style={{ color: 'var(--accent-india)', textDecoration: 'none' }}>{t('indic_ug')}</a>) & <a href="https://acube.di.unipi.it/" target="_blank" style={{ color: 'var(--accent-italy)', textDecoration: 'none' }}>Acube Lab</a>
                </span>
                <span style={{ opacity: 0.3 }}>|</span>
                <span>{t('licence')} <a href="https://github.com/ftosoni/code-search-engine/blob/main/LICENSE.md" target="_blank" style={{ color: 'inherit' }}>Apache 2.0</a></span>
                <span style={{ opacity: 0.3 }}>|</span>
                <span><a href="https://github.com/ftosoni/code-search-engine" target="_blank" style={{ color: 'inherit', textDecoration: 'none' }}>{t('view_source')}</a></span>
                <span style={{ opacity: 0.3 }}>|</span>
                <span><a href="https://archive.softwareheritage.org/browse/origin/directory/?origin_url=https://github.com/ftosoni/mediawiki-code2code-search" target="_blank" style={{ color: 'inherit', textDecoration: 'none' }}>{t('view_swhid')}</a></span>
                <span style={{ opacity: 0.3 }}>|</span>
                <span><a href="https://github.com/ftosoni/mediawiki-code2code-search/issues" target="_blank" style={{ color: 'inherit', textDecoration: 'none' }}>{t('issues')}</a></span>
                <span style={{ opacity: 0.3 }}>|</span>
                <div style={{ width: '100%', marginTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '1.5rem', color: '#666', display: 'flex', justifyContent: 'center', gap: '2rem' }}>
                    <span>2026-04-08</span>
                    <span>
                        {t('sloan_grant_prefix')}
                        <a href="https://sloan.org/" target="_blank" style={{ color: 'inherit' }}>Alfred P. Sloan Foundation</a>
                        {t('sloan_grant_mid')}
                        <a href="https://sloan.org/grant-detail/g-2025-25193" target="_blank" style={{ color: 'inherit' }}>G-2025-25193</a>
                        {t('sloan_grant_suffix')}
                    </span>
                </div>
            </footer>
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
