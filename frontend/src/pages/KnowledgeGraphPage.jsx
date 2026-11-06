import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Share2, ArrowRight, Waypoints } from "lucide-react";
import KnowledgeGraphView from "../components/KnowledgeGraphView.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { getDomainGraph, getDomainDetail, getDomainInference, getSemanticPath } from "../services/api.js";
import { niveauLabel } from "../components/CourseCard.jsx";
import { useToast } from "../context/ToastContext.jsx";

export default function KnowledgeGraphPage() {
  const [graph, setGraph] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [inference, setInference] = useState(null);
  const [loading, setLoading] = useState(true);
  const { notify } = useToast();

  const [pathSource, setPathSource] = useState("");
  const [pathTarget, setPathTarget] = useState("");
  const [pathResult, setPathResult] = useState(null);
  const [pathLoading, setPathLoading] = useState(false);

  useEffect(() => {
    getDomainGraph()
      .then((g) => {
        setGraph(g);
        if (g.nodes.length >= 2) {
          setPathSource(g.nodes[0].id);
          setPathTarget(g.nodes[g.nodes.length - 1].id);
        }
      })
      .catch(() => notify("Impossible de charger le Knowledge Graph (Fuseki est-il lancé ?)"))
      .finally(() => setLoading(false));
  }, [notify]);

  useEffect(() => {
    if (!selectedId) { setDetail(null); setInference(null); return; }
    getDomainDetail(selectedId).then(setDetail).catch(() => notify("Impossible de charger le détail de ce domaine."));
    getDomainInference(selectedId).then(setInference).catch(() => setInference(null));
  }, [selectedId, notify]);

  function handleFindPath(e) {
    e.preventDefault();
    if (!pathSource || !pathTarget) return;
    setPathLoading(true);
    setPathResult(null);
    getSemanticPath(pathSource, pathTarget)
      .then(setPathResult)
      .catch(() => notify("Impossible de calculer le chemin sémantique."))
      .finally(() => setPathLoading(false));
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Knowledge Graph</h1>
        <p>Explorez la hiérarchie des domaines de l'ontologie RDF/OWL — cliquez sur un nœud pour le détailler.</p>
      </div>

      {loading && <div className="skeleton" style={{ height: 560, borderRadius: "var(--radius)" }} />}

      {!loading && (!graph || graph.nodes.length === 0) && (
        <EmptyState icon={Share2} title="Graphe indisponible" message="Vérifie que Fuseki tourne bien sur le port 3030." />
      )}

      {!loading && graph && graph.nodes.length > 0 && (
        <div className="course-detail-grid">
          <KnowledgeGraphView
            nodes={graph.nodes}
            edges={graph.edges}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />

          <div className="card card-pad" style={{ minHeight: 200 }}>
            {!detail ? (
              <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Sélectionnez un domaine dans le graphe pour voir ses cours et compétences associées.</p>
            ) : (
              <>
                <p style={{ fontSize: 11, textTransform: "uppercase", color: "var(--text-faint)", marginBottom: 4 }}>Domain</p>
                <h3 style={{ fontSize: 18, marginBottom: 14 }}>{detail.label}</h3>

                {inference && inference.chaine.length > 1 && (
                  <div style={{ marginBottom: 18 }}>
                    <p style={{ fontSize: 12.5, fontWeight: 700, color: "var(--text-muted)", marginBottom: 8 }}>
                      Knowledge Graph Inference
                    </p>
                    <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 6, marginBottom: 6 }}>
                      {inference.chaine.map((node, i) => (
                        <span key={node.local_name} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          <span className={`badge ${i === 0 ? "badge-primary" : "badge-graph"}`}>{node.label}</span>
                          {i < inference.chaine.length - 1 && <ArrowRight size={13} style={{ color: "var(--text-faint)" }} />}
                        </span>
                      ))}
                    </div>
                    <p style={{ fontSize: 11.5, color: "var(--text-faint)" }}>
                      Relation déduite par raisonnement OWL (:sousDomaineDe déclarée owl:TransitiveProperty) —
                      jamais affirmée directement dans l'ontologie.
                    </p>
                  </div>
                )}

                {detail.competences.length > 0 && (
                  <div style={{ marginBottom: 18 }}>
                    <p style={{ fontSize: 12.5, fontWeight: 700, color: "var(--text-muted)", marginBottom: 8 }}>Related concepts</p>
                    <div className="skills-list">
                      {detail.competences.map((c) => <span key={c} className="badge badge-semantic">{c}</span>)}
                    </div>
                  </div>
                )}

                <p style={{ fontSize: 12.5, fontWeight: 700, color: "var(--text-muted)", marginBottom: 8 }}>
                  Related courses ({detail.cours.length})
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 280, overflowY: "auto" }}>
                  {detail.cours.map((c) => (
                    <Link key={c.doc_id} to={`/courses/${c.doc_id}`} className="compare-mini-card" style={{ display: "block" }}>
                      <p className="title" style={{ margin: 0 }}>{c.titre}</p>
                      <p className="score">{niveauLabel(c.niveau)} · {c.duree_heures}h</p>
                    </Link>
                  ))}
                  {detail.cours.length === 0 && <p style={{ fontSize: 12.5, color: "var(--text-faint)" }}>Aucun cours direct dans ce domaine.</p>}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {!loading && graph && graph.nodes.length > 1 && (
        <div className="card card-pad fade-in path-finder-card" style={{ marginTop: 20 }}>
          <p className="search-intelligence-title" style={{ marginBottom: 4 }}>
            <Waypoints size={13} /> Find semantic path
          </p>
          <p className="path-finder-subtitle">
            Trouve le plus court chemin entre deux domaines dans le graphe de connaissances.
          </p>

          <form onSubmit={handleFindPath} className="path-finder-form">
            <select
              className="path-finder-select"
              value={pathSource}
              onChange={(e) => setPathSource(e.target.value)}
            >
              {graph.nodes.map((n) => <option key={n.id} value={n.id}>{n.label}</option>)}
            </select>
            <ArrowRight size={15} className="path-finder-arrow" />
            <select
              className="path-finder-select"
              value={pathTarget}
              onChange={(e) => setPathTarget(e.target.value)}
            >
              {graph.nodes.map((n) => <option key={n.id} value={n.id}>{n.label}</option>)}
            </select>
            <button type="submit" className="btn btn-primary btn-sm path-finder-btn" disabled={pathLoading || !pathSource || !pathTarget}>
              {pathLoading ? "Recherche..." : "Find path"}
            </button>
          </form>

          {pathResult && pathResult.trouve && (
            <div className="path-finder-result">
              {pathResult.chemin.map((node, i) => (
                <span key={node.local_name} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span className="badge badge-graph">{node.label}</span>
                  {i < pathResult.chemin.length - 1 && <ArrowRight size={13} style={{ color: "var(--text-faint)" }} />}
                </span>
              ))}
            </div>
          )}
          {pathResult && !pathResult.trouve && (
            <p className="path-finder-empty">Aucun chemin trouvé entre ces deux domaines.</p>
          )}
        </div>
      )}
    </div>
  );
}
