const MODES = [
  { id: "lexical", label: "Lexical", desc: "Recherche basée sur la correspondance des mots (BM25)." },
  { id: "semantic", label: "Semantic", desc: "Recherche basée sur le sens de la requête (embeddings)." },
  { id: "hybrid", label: "Hybrid", desc: "Combine les deux et enrichit via le Knowledge Graph." },
];

export default function SearchModeSelector({ mode, onChange }) {
  return (
    <div className="mode-selector">
      {MODES.map((m) => (
        <div
          key={m.id}
          className={`mode-option ${mode === m.id ? "selected" : ""}`}
          onClick={() => onChange(m.id)}
          role="radio"
          aria-checked={mode === m.id}
          tabIndex={0}
        >
          <strong>{m.label}</strong>
          <span>{m.desc}</span>
        </div>
      ))}
    </div>
  );
}
