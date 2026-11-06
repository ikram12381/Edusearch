const NIVEAUX = [
  { id: "Debutant", label: "Beginner" },
  { id: "Intermediaire", label: "Intermediate" },
  { id: "Avance", label: "Advanced" },
];

const DURATIONS = [
  { id: "5", label: "< 5h" },
  { id: "10", label: "5–10h" },
  { id: "20", label: "10–20h" },
  { id: "999", label: "> 20h" },
];

const RATINGS = [
  { id: "4", label: "4+" },
  { id: "4.5", label: "4.5+" },
];

export default function Filters({ domains, value, onChange }) {
  function set(key, val) {
    onChange({ ...value, [key]: value[key] === val ? undefined : val });
  }

  return (
    <div className="filters-panel">
      <div className="filter-group">
        <span className="filter-group-title">Domain</span>
        <div className="filter-options">
          {domains.map((d) => (
            <label key={d.id} className={`filter-option ${value.domaine === d.id ? "active" : ""}`}>
              <input type="radio" checked={value.domaine === d.id} onChange={() => set("domaine", d.id)} />
              {d.label}
            </label>
          ))}
        </div>
      </div>

      <div className="filter-group">
        <span className="filter-group-title">Difficulty</span>
        <div className="filter-options">
          {NIVEAUX.map((n) => (
            <label key={n.id} className={`filter-option ${value.niveau === n.id ? "active" : ""}`}>
              <input type="radio" checked={value.niveau === n.id} onChange={() => set("niveau", n.id)} />
              {n.label}
            </label>
          ))}
        </div>
      </div>

      <div className="filter-group">
        <span className="filter-group-title">Duration</span>
        <div className="filter-options">
          {DURATIONS.map((d) => (
            <label key={d.id} className={`filter-option ${value.duree_max === d.id ? "active" : ""}`}>
              <input type="radio" checked={value.duree_max === d.id} onChange={() => set("duree_max", d.id)} />
              {d.label}
            </label>
          ))}
        </div>
      </div>

      <div className="filter-group">
        <span className="filter-group-title">Rating</span>
        <div className="filter-options">
          {RATINGS.map((r) => (
            <label key={r.id} className={`filter-option ${value.note_min === r.id ? "active" : ""}`}>
              <input type="radio" checked={value.note_min === r.id} onChange={() => set("note_min", r.id)} />
              {r.label}
            </label>
          ))}
        </div>
      </div>

      <div className="filter-group">
        <span className="filter-group-title">Price</span>
        <div className="filter-options">
          <label className={`filter-option ${value.gratuit === "true" ? "active" : ""}`}>
            <input type="radio" checked={value.gratuit === "true"} onChange={() => set("gratuit", "true")} />
            Free
          </label>
          <label className={`filter-option ${value.gratuit === "false" ? "active" : ""}`}>
            <input type="radio" checked={value.gratuit === "false"} onChange={() => set("gratuit", "false")} />
            Paid
          </label>
        </div>
      </div>

      {Object.values(value).some(Boolean) && (
        <button className="btn btn-ghost btn-sm" onClick={() => onChange({})}>Clear filters</button>
      )}
    </div>
  );
}
