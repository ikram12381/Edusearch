import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Search as SearchIcon, Database, Brain, Sparkles } from "lucide-react";
import { compareSearch } from "../services/api.js";
import { domainLabel } from "../components/CourseCard.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { useToast } from "../context/ToastContext.jsx";

const COLUMNS = [
  { key: "lexical", label: "Lexical Search", icon: Database, desc: "Résultats basés sur BM25.", color: "var(--lexical)" },
  { key: "semantic", label: "Semantic Search", icon: Brain, desc: "Résultats basés sur les embeddings.", color: "var(--semantic)" },
  { key: "hybrid", label: "Hybrid Search", icon: Sparkles, desc: "Résultats combinés + Knowledge Graph.", color: "var(--primary)" },
];

export default function CompareSearch() {
  const [params] = useSearchParams();
  const [query, setQuery] = useState(params.get("q") || "");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const { notify } = useToast();

  async function run(q) {
    const trimmed = q.trim();
    if (!trimmed) return;
    setLoading(true);
    try {
      const res = await compareSearch(trimmed, 6);
      setData(res);
    } catch (err) {
      notify(err.message || "Impossible de comparer les stratégies de recherche.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (params.get("q")) run(params.get("q"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSubmit(e) {
    e.preventDefault();
    run(query);
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Compare Search</h1>
        <p>Une seule requête, trois stratégies : observez ce que chaque méthode apporte.</p>
      </div>

      <form className="search-hero" onSubmit={handleSubmit} style={{ marginBottom: 24 }}>
        <div className="search-input-row">
          <input
            type="text"
            placeholder="Je veux apprendre la reconnaissance d'image"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="btn btn-primary" disabled={loading || !query.trim()}>
            <SearchIcon size={15} /> Compare
          </button>
        </div>
      </form>

      {loading && (
        <div style={{ display: "flex", alignItems: "center", gap: 10, color: "var(--text-muted)", fontSize: 13.5 }}>
          <span className="spinner" /> Exécution des trois stratégies en parallèle…
        </div>
      )}

      {!loading && !data && (
        <EmptyState icon={SearchIcon} title="Comparez les stratégies de recherche" message="Saisissez une requête pour voir Lexical, Semantic et Hybrid côte à côte." />
      )}

      {!loading && data && (
        <>
          <div className="card card-pad" style={{ marginBottom: 20 }}>
            <p style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--text-faint)", marginBottom: 6 }}>Query</p>
            <p style={{ fontFamily: "var(--font-mono)", fontSize: 14 }}>"{query}"</p>
          </div>

          <div className="compare-grid">
            {COLUMNS.map(({ key, label, icon: Icon, desc, color }) => {
              const results = data[key]?.results || [];
              return (
                <div key={key} className="compare-column">
                  <div className="compare-column-header">
                    <Icon size={16} color={color} />
                    <div>
                      <h3>{label}</h3>
                      <p style={{ fontSize: 11.5, color: "var(--text-muted)" }}>{desc}</p>
                    </div>
                  </div>

                  {results.length === 0 && <p style={{ fontSize: 12.5, color: "var(--text-faint)", padding: "0 4px" }}>Aucun résultat.</p>}

                  {results.map((r, idx) => (
                    <Link to={`/courses/${r.doc_id}`} key={r.doc_id} className="compare-mini-card">
                      <p className="rank">#{idx + 1}</p>
                      <p className="title">{r.titre}</p>
                      <p className="score">{domainLabel(r.domaine)} · score {Math.round(r.score_final * 100)}%</p>
                    </Link>
                  ))}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
