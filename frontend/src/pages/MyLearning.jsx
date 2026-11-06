import { useState } from "react";
import { Link } from "react-router-dom";
import { GraduationCap } from "lucide-react";
import ProgressBar from "../components/ProgressBar.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { domainLabel, niveauLabel } from "../components/CourseCard.jsx";
import { MY_LEARNING } from "../services/mockData.js";
import { useFavorites } from "../context/FavoritesContext.jsx";

const TABS = ["In Progress", "Completed", "Saved"];

export default function MyLearning() {
  const [tab, setTab] = useState("In Progress");
  const { favorites } = useFavorites();

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>My Learning</h1>
        <p>Suivez votre progression sur vos cours.</p>
      </div>

      <div className="mode-selector" style={{ maxWidth: 420 }}>
        {TABS.map((t) => (
          <div key={t} className={`chip ${tab === t ? "active" : ""}`} onClick={() => setTab(t)} style={{ flex: 1, textAlign: "center" }}>
            {t}
          </div>
        ))}
      </div>

      {tab === "In Progress" && (
        <div className="grid-cols-3" style={{ marginTop: 18 }}>
          {MY_LEARNING.inProgress.map((c) => (
            <div key={c.doc_id} className="course-card">
              <Link to={`/courses/${c.doc_id}`} className="course-card-title">{c.titre}</Link>
              <p className="course-card-meta">{domainLabel(c.domaine)} · {niveauLabel(c.niveau)}</p>
              <ProgressBar value={c.progress} />
              <Link to={`/courses/${c.doc_id}`} className="btn btn-primary btn-sm btn-block">Continue</Link>
            </div>
          ))}
        </div>
      )}

      {tab === "Completed" && (
        <div className="grid-cols-3" style={{ marginTop: 18 }}>
          {MY_LEARNING.completed.map((c) => (
            <div key={c.doc_id} className="course-card">
              <Link to={`/courses/${c.doc_id}`} className="course-card-title">{c.titre}</Link>
              <p className="course-card-meta">{domainLabel(c.domaine)} · {niveauLabel(c.niveau)}</p>
              <span className="badge badge-success" style={{ alignSelf: "flex-start" }}>Completed</span>
            </div>
          ))}
        </div>
      )}

      {tab === "Saved" && (
        favorites.length === 0 ? (
          <EmptyState icon={GraduationCap} title="Aucun cours sauvegardé" message="Enregistrez des cours depuis la recherche ou le catalogue pour les retrouver ici." />
        ) : (
          <p style={{ marginTop: 18, fontSize: 13, color: "var(--text-muted)" }}>
            Voir votre liste complète dans <Link to="/favorites" style={{ color: "var(--primary)", fontWeight: 600 }}>Favorites</Link>.
          </p>
        )
      )}
    </div>
  );
}
