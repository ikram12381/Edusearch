import { useEffect, useState } from "react";
import { BarChart3, RefreshCw } from "lucide-react";
import EmptyState from "../components/EmptyState.jsx";
import { getEvaluation } from "../services/api.js";
import { useToast } from "../context/ToastContext.jsx";

const METRICS = [
  { key: "precision", label: "Precision@5" },
  { key: "recall", label: "Recall@5" },
  { key: "ndcg", label: "NDCG@5" },
];

const STRATEGIES = [
  { key: "lexical", label: "Lexical", color: "var(--lexical)" },
  { key: "vectoriel", label: "Semantic", color: "var(--semantic)" },
  { key: "hybride", label: "Hybrid", color: "var(--primary)" },
];

export default function Evaluation() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { notify } = useToast();

  function load() {
    setLoading(true);
    getEvaluation(5)
      .then(setData)
      .catch(() => notify("Impossible de calculer l'évaluation (Elasticsearch/Fuseki actifs requis)."))
      .finally(() => setLoading(false));
  }

  useEffect(load, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="fade-in">
      <div className="page-header-row">
        <div className="page-header">
          <h1>Search Evaluation</h1>
          <p>Précision@5 / Rappel@5 / NDCG@5, calculés en direct sur le jeu de test — hybride vs. chaque composante isolée.</p>
        </div>
        <button className="btn btn-secondary" onClick={load} disabled={loading}>
          <RefreshCw size={15} className={loading ? "spinner" : ""} /> Recalculer
        </button>
      </div>

      {loading && <div className="skeleton" style={{ height: 340, borderRadius: "var(--radius)" }} />}

      {!loading && !data && (
        <EmptyState icon={BarChart3} title="Évaluation indisponible" message="Vérifie que le backend, Elasticsearch et Fuseki tournent." />
      )}

      {!loading && data && (
        <>
          <div className="card card-pad" style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: 15, marginBottom: 18 }}>Comparaison des performances (k = {data.k})</h3>
            <div className="bar-chart">
              {METRICS.map(({ key, label }) => (
                <div className="bar-chart-row" key={key}>
                  <span className="bar-chart-row-label">{label}</span>
                  <div className="bar-chart-bars">
                    {STRATEGIES.map((s) => {
                      const value = data[s.key][key];
                      return (
                        <div className="bar-chart-bar" key={s.key}>
                          <span className="bar-chart-bar-value">{value.toFixed(2)}</span>
                          <div className="bar-chart-bar-fill" style={{ height: `${value * 100}%`, background: s.color }} />
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
            <div className="bar-chart-legend" style={{ marginTop: 16 }}>
              {STRATEGIES.map((s) => (
                <span key={s.key}><i style={{ background: s.color }} /> {s.label}</span>
              ))}
            </div>
          </div>

          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Métrique (@{data.k})</th>
                  {STRATEGIES.map((s) => <th key={s.key}>{s.label}</th>)}
                </tr>
              </thead>
              <tbody>
                {METRICS.map(({ key, label }) => (
                  <tr key={key}>
                    <td>{label}</td>
                    {STRATEGIES.map((s) => <td className="num" key={s.key}>{data[s.key][key].toFixed(3)}</td>)}
                  </tr>
                ))}
                <tr>
                  <td>Temps de réponse moyen (ms)</td>
                  {STRATEGIES.map((s) => <td className="num" key={s.key}>{data[s.key].avg_response_time_ms.toFixed(1)}</td>)}
                </tr>
              </tbody>
            </table>
          </div>

          <h3 style={{ fontSize: 15, margin: "28px 0 12px" }}>Détail par requête — système hybride</h3>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr><th>Requête</th><th>Precision</th><th>Recall</th><th>NDCG</th><th>Temps (ms)</th></tr>
              </thead>
              <tbody>
                {data.hybride.par_requete.map((q) => (
                  <tr key={q.query}>
                    <td>{q.query}</td>
                    <td className="num">{q.precision.toFixed(2)}</td>
                    <td className="num">{q.recall.toFixed(2)}</td>
                    <td className="num">{q.ndcg.toFixed(2)}</td>
                    <td className="num">{q.response_time_ms.toFixed(0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
