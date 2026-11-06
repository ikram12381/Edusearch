import Modal from "./Modal.jsx";

function ScoreRow({ label, value, color }) {
  const pct = Math.round((value || 0) * 100);
  return (
    <div className="score-row">
      <span className="score-row-label">{label}</span>
      <div className="score-row-track">
        <div className="score-row-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="score-row-value">{pct}%</span>
    </div>
  );
}

export default function SearchExplanation({ result, onClose }) {
  if (!result) return null;
  return (
    <Modal title="Why this result?" onClose={onClose} maxWidth={480}>
      <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>{result.titre}</p>

      <ScoreRow label="Lexical relevance" value={result.score_lexical} color="var(--lexical)" />
      <ScoreRow label="Semantic similarity" value={result.score_vectoriel} color="var(--semantic)" />
      <ScoreRow label="Knowledge Graph" value={result.score_graphe} color="var(--graph)" />
      <div style={{ height: 1, background: "var(--border)", margin: "12px 0" }} />
      <ScoreRow label="Final Hybrid Score" value={result.score_final} color="var(--primary)" />

      {result.exclu && (
        <div className="banner-error" style={{ marginTop: 14 }}>{result.raison_exclusion}</div>
      )}

      {result.matched_concepts?.length > 0 && (
        <div style={{ marginTop: 18 }}>
          <p style={{ fontSize: 12.5, fontWeight: 700, color: "var(--text-muted)", marginBottom: 8 }}>Matched concepts</p>
          <div className="concept-chips">
            {result.matched_concepts.map((c) => <span key={c} className="badge badge-primary">{c}</span>)}
          </div>
        </div>
      )}

      {result.related_concepts?.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <p style={{ fontSize: 12.5, fontWeight: 700, color: "var(--text-muted)", marginBottom: 8 }}>Related concepts</p>
          <div className="concept-chips">
            {result.related_concepts.map((c) => <span key={c} className="badge">{c}</span>)}
          </div>
        </div>
      )}

      {result.trouve_par_expansion_graphe && (
        <p style={{ fontSize: 12, color: "var(--graph)", marginTop: 14 }}>
          Trouvé uniquement grâce à l'expansion sémantique du Knowledge Graph — aucune correspondance lexicale ou vectorielle directe.
        </p>
      )}
    </Modal>
  );
}
