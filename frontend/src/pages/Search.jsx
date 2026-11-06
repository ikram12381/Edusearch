import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Search as SearchIcon, GitCompare, Sparkles } from "lucide-react";
import SearchModeSelector from "../components/SearchModeSelector.jsx";
import Filters from "../components/Filters.jsx";
import SearchExplanation from "../components/SearchExplanation.jsx";
import LoadingSteps from "../components/LoadingSteps.jsx";
import EmptyState from "../components/EmptyState.jsx";
import PrerequisiteGraph from "../components/PrerequisiteGraph.jsx";
import { domainLabel, niveauLabel } from "../components/CourseCard.jsx";
import { useFavorites } from "../context/FavoritesContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
import { searchCourses, getConfig, getDomainGraph, getCourseGraph } from "../services/api.js";

const LIVE_DEBOUNCE_MS = 450;

export default function Search() {
  const [params] = useSearchParams();
  const [query, setQuery] = useState(params.get("q") || "");
  const [mode, setMode] = useState("hybrid");
  const [results, setResults] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [filters, setFilters] = useState({});
  const [domains, setDomains] = useState([]);
  const [config, setConfig] = useState(null);
  const [explainResult, setExplainResult] = useState(null);
  const [openGraphFor, setOpenGraphFor] = useState(null);
  const [graphInfo, setGraphInfo] = useState({});
  const [expandedEntities, setExpandedEntities] = useState({});

  const { isFavorite, toggleFavorite } = useFavorites();
  const { notify } = useToast();
  const debounceRef = useRef(null);
  const abortRef = useRef(null);

  useEffect(() => {
    getDomainGraph().then((g) => setDomains(g.nodes.map((n) => ({ id: n.id, label: n.label })))).catch(() => {});
    getConfig().then(setConfig).catch(() => {});
  }, []);

  const runSearch = useCallback(
    async (q, searchMode) => {
      const trimmed = q.trim();
      if (!trimmed) return;
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      setHasSearched(true);
      try {
        const data = await searchCourses(trimmed, { mode: searchMode, top_k: 12, signal: controller.signal });
        setResults(data.results);
        setMeta({
          nb_lexical: data.nb_lexical,
          nb_vectoriel: data.nb_vectoriel,
          nb_exclus: data.nb_exclus,
          entites: data.entites_detectees || [],
          domainesElargis: data.domaines_elargis || [],
        });
      } catch (err) {
        if (err.name === "AbortError") return;
        notify(err.message || "Search service temporarily unavailable. Please try again.");
      } finally {
        setLoading(false);
      }
    },
    [notify]
  );

  useEffect(() => {
    if (params.get("q")) runSearch(params.get("q"), mode);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSubmit(e) {
    e.preventDefault();
    clearTimeout(debounceRef.current);
    runSearch(query, mode);
  }

  function handleChange(e) {
    const value = e.target.value;
    setQuery(value);
    clearTimeout(debounceRef.current);
    if (!value.trim()) return;
    debounceRef.current = setTimeout(() => runSearch(value, mode), LIVE_DEBOUNCE_MS);
  }

  function handleModeChange(m) {
    setMode(m);
    if (query.trim()) runSearch(query, m);
  }

  async function toggleGraphDetails(docId) {
    if (openGraphFor === docId) { setOpenGraphFor(null); return; }
    setOpenGraphFor(docId);
    if (!graphInfo[docId]) {
      try {
        const data = await getCourseGraph(docId);
        setGraphInfo((prev) => ({ ...prev, [docId]: data }));
      } catch {
        notify("Le graphe de connaissances n'a pas répondu (Fuseki est-il lancé ?)");
      }
    }
  }

  const filteredResults = useMemo(() => {
    return results.filter((r) => {
      if (filters.domaine && r.domaine !== filters.domaine) return false;
      if (filters.niveau && r.niveau !== filters.niveau) return false;
      if (filters.duree_max && r.duree_heures != null && r.duree_heures > Number(filters.duree_max)) return false;
      if (filters.note_min && r.note != null && r.note < Number(filters.note_min)) return false;
      if (filters.gratuit && r.gratuit != null && String(r.gratuit) !== filters.gratuit) return false;
      return true;
    });
  }, [results, filters]);

  return (
    <div className="fade-in">
      <div className="page-header-row">
        <div className="page-header">
          <h1>Intelligent Search</h1>
          <p>Query in natural language — the engine understands meaning, not just keywords.</p>
        </div>
        <Link to={`/compare${query ? `?q=${encodeURIComponent(query)}` : ""}`} className="btn btn-secondary">
          <GitCompare size={15} /> Compare Search
        </Link>
      </div>

      <div className="search-hero">
        <form className="search-input-row" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="I want to learn how neural networks are used for image recognition"
            value={query}
            onChange={handleChange}
            autoFocus
          />
          {loading && <span className="spinner" style={{ alignSelf: "center", marginRight: 10 }} />}
          <button type="submit" className="btn btn-primary" disabled={loading || !query.trim()}>
            <SearchIcon size={15} /> Search
          </button>
        </form>

        <SearchModeSelector mode={mode} onChange={handleModeChange} />
      </div>

      {loading && <LoadingSteps active={loading} />}

      {!loading && meta && (meta.entites.length > 0 || meta.domainesElargis.length > 0 || config) && (
        <div className="search-intelligence fade-in" style={{ marginBottom: 18 }}>
          <p className="search-intelligence-title"><Sparkles size={13} /> Search Intelligence</p>

          {meta.entites.length > 0 && (
            <>
              <p style={{ fontSize: 12.5, color: "var(--text-muted)", marginBottom: 8 }}>Concept(s) détecté(s) dans la requête :</p>
              <div className="concept-chips" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {meta.entites.map((ent) => {
                  const expanded = !!expandedEntities[ent.label];
                  return (
                    <div key={ent.label}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                        <span className={`badge ${ent.ambigu ? "badge-graph" : "badge-primary"}`}>{ent.label}</span>
                        {ent.ambigu ? (
                          <span style={{ fontSize: 11.5, color: "var(--graph, var(--text-faint))" }}>⚠ Concept ambigu</span>
                        ) : (
                          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Type : <strong style={{ color: "var(--text)" }}>{ent.type_retenu}</strong></span>
                        )}
                        <span style={{ fontSize: 12, color: "var(--success, var(--text-muted))" }}>✓ Retenu : <strong>{ent.type_retenu}</strong></span>
                        {ent.ambigu && ent.interpretations?.length > 0 && (
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            style={{ padding: "2px 8px", fontSize: 11.5 }}
                            onClick={() => setExpandedEntities((s) => ({ ...s, [ent.label]: !expanded }))}
                          >
                            {expanded ? "Masquer les interprétations" : "Voir les interprétations"}
                          </button>
                        )}
                      </div>

                      {expanded && ent.interpretations?.length > 0 && (
                        <div style={{ marginTop: 8, marginLeft: 4, display: "flex", flexDirection: "column", gap: 6 }}>
                          {ent.interpretations.map((interp) => (
                            <div key={interp.type} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                              <span style={{ fontSize: 12, width: 90, flexShrink: 0, color: interp.type === ent.type_retenu ? "var(--text)" : "var(--text-muted)" }}>
                                {interp.type === ent.type_retenu ? "✓ " : ""}{interp.type}
                              </span>
                              <div className="progress-track" style={{ flex: 1, maxWidth: 160 }}>
                                <div className="progress-fill" style={{ width: `${Math.round(interp.score * 100)}%` }} />
                              </div>
                              <span style={{ fontSize: 12, fontWeight: 700, width: 36 }}>{Math.round(interp.score * 100)}%</span>
                            </div>
                          ))}
                          {ent.raison_resolution && (
                            <p style={{ fontSize: 11.5, color: "var(--text-faint)", marginTop: 4 }}>
                              💡 Pourquoi ? {ent.raison_resolution}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          )}

          {meta.domainesElargis.length > 0 && (
            <p style={{ fontSize: 12.5, color: "var(--text-muted)", marginTop: 10 }}>
              Expanded via Knowledge Graph to related domains: <strong style={{ color: "var(--text)" }}>{meta.domainesElargis.map(domainLabel).join(", ")}</strong>
            </p>
          )}

          {mode === "hybrid" && config && (
            <div className="strategy-row" style={{ marginTop: 14 }}>
              <p style={{ fontSize: 12.5, fontWeight: 700 }}>Search strategy — Hybrid Search</p>
              {[
                ["Lexical", config.poids_lexical, "var(--lexical)"],
                ["Semantic", config.poids_vectoriel, "var(--semantic)"],
                ["Knowledge Graph", config.poids_graphe + config.poids_expansion, "var(--graph)"],
              ].map(([label, val, color]) => (
                <div className="score-row" key={label}>
                  <span className="score-row-label">{label}</span>
                  <div className="score-row-track"><div className="score-row-fill" style={{ width: `${val * 100}%`, background: color }} /></div>
                  <span className="score-row-value">{Math.round(val * 100)}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="search-layout">
        <Filters domains={domains} value={filters} onChange={setFilters} />

        <div className="results-column">
          {!loading && hasSearched && filteredResults.length === 0 && (
            <EmptyState icon={SearchIcon} title="No courses found" message="Try a different query, mode, or clear your filters." />
          )}

          {!hasSearched && !loading && (
            <EmptyState icon={SearchIcon} title="Search for a course" message="Try: 'I want to learn how neural networks are used for image recognition'." />
          )}

          {filteredResults.map((r, idx) => (
            <div key={r.doc_id} className={`card card-pad result-card ${r.exclu ? "excluded" : ""} fade-in-up`} style={{ animationDelay: `${idx * 40}ms` }}>
              <div className="result-card-top">
                <div>
                  <Link to={`/courses/${r.doc_id}`} className="course-card-title">{r.titre}</Link>
                  <p className="course-card-meta">
                    {domainLabel(r.domaine)} · {niveauLabel(r.niveau)}
                    {r.duree_heures != null ? ` · ${r.duree_heures}h` : ""}
                    {r.formateur ? ` · ${r.formateur}` : ""}
                  </p>
                </div>
                <div className="result-card-score">
                  <span className="result-card-score-value">{Math.round(r.score_final * 100)}%</span>
                  <span className="result-card-score-label">{mode} relevance</span>
                </div>
              </div>

              <p className="course-card-desc" style={{ WebkitLineClamp: 3 }}>{r.description}</p>

              <div className="badge-row concept-chips">
                {r.note != null && <span className="badge">★ {r.note.toFixed(1)}</span>}
                {r.gratuit != null && <span className={`badge ${r.gratuit ? "badge-success" : ""}`}>{r.gratuit ? "Free" : "Paid"}</span>}
                {mode === "hybrid" && (
                  <>
                    <span className="badge badge-lexical">lexical {Math.round(r.score_lexical * 100)}%</span>
                    <span className="badge badge-semantic">semantic {Math.round(r.score_vectoriel * 100)}%</span>
                    {r.score_expansion_domaine > 0 && (
                      <span className="badge badge-graph">{r.trouve_par_expansion_graphe ? "found via graph" : "expanded domain"}</span>
                    )}
                  </>
                )}
                {r.exclu && <span className="badge badge-danger">{r.raison_exclusion}</span>}
              </div>

              <div className="result-card-actions">
                <button className="btn btn-secondary btn-sm" onClick={() => setExplainResult(r)}>Why this result?</button>
                <button className="btn btn-ghost btn-sm" onClick={() => toggleGraphDetails(r.doc_id)}>
                  {openGraphFor === r.doc_id ? "Hide prerequisite graph" : "View prerequisite graph"}
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => toggleFavorite(r.doc_id)}>
                  {isFavorite(r.doc_id) ? "★ Saved" : "☆ Save"}
                </button>
                <Link to={`/courses/${r.doc_id}`} className="btn btn-ghost btn-sm">View Course</Link>
              </div>

              {openGraphFor === r.doc_id && (
                <div style={{ marginTop: 6, paddingTop: 14, borderTop: "1px solid var(--border)" }}>
                  {!graphInfo[r.doc_id] ? (
                    <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12.5, color: "var(--text-muted)" }}>
                      <span className="spinner" /> Interrogation du triplestore…
                    </div>
                  ) : (
                    <PrerequisiteGraph rootTitle={r.titre} chain={graphInfo[r.doc_id].chaine_prerequis} />
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {explainResult && <SearchExplanation result={explainResult} onClose={() => setExplainResult(null)} />}
    </div>
  );
}
