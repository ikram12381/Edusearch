import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Star, Clock, BookOpen, Bookmark, Share2 } from "lucide-react";
import { getCourse } from "../services/api.js";
import { domainLabel, niveauLabel } from "../components/CourseCard.jsx";
import PrerequisiteGraph from "../components/PrerequisiteGraph.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { useFavorites } from "../context/FavoritesContext.jsx";
import { useToast } from "../context/ToastContext.jsx";

export default function CourseDetails() {
  const { docId } = useParams();
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showGraph, setShowGraph] = useState(false);
  const { isFavorite, toggleFavorite } = useFavorites();
  const { notify } = useToast();

  useEffect(() => {
    setLoading(true);
    setShowGraph(false);
    getCourse(docId)
      .then(setCourse)
      .catch(() => notify("Impossible de charger ce cours."))
      .finally(() => setLoading(false));
  }, [docId, notify]);

  if (loading) {
    return <div className="skeleton" style={{ height: 320, borderRadius: "var(--radius)" }} />;
  }

  if (!course) {
    return <EmptyState icon={BookOpen} title="Cours introuvable" message="Ce cours n'existe pas ou plus." />;
  }

  const fav = isFavorite(course.doc_id);

  return (
    <div className="fade-in">
      <div className="course-hero">
        <div className="course-hero-badges">
          <span className="badge badge-primary">{domainLabel(course.domaine)}</span>
          <span className="badge">{niveauLabel(course.niveau)}</span>
          <span className="badge"><Clock size={11} /> {course.duree_heures}h</span>
          <span className={`badge ${course.gratuit ? "badge-success" : ""}`}>{course.gratuit ? "Free" : "Paid"}</span>
        </div>
        <div className="page-header-row">
          <h1 style={{ fontSize: 28, maxWidth: 640 }}>{course.titre}</h1>
          <div style={{ display: "flex", gap: 8 }}>
            <button className={`btn-icon ${fav ? "active" : ""}`} onClick={() => toggleFavorite(course.doc_id)} aria-label="Favori">
              <Bookmark size={16} />
            </button>
            <button className="btn-icon" aria-label="Partager"><Share2 size={16} /></button>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 14, fontWeight: 600 }}>
          <Star size={15} style={{ fill: "#f59e0b", color: "#f59e0b" }} /> {course.note?.toFixed(1)}
        </div>
      </div>

      <div className="course-detail-grid">
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div className="card card-pad">
            <h3 style={{ fontSize: 15, marginBottom: 10 }}>Description</h3>
            <p style={{ fontSize: 14, lineHeight: 1.6, color: "var(--text-muted)" }}>{course.description}</p>
          </div>

          {course.competences_enseignees.length > 0 && (
            <div className="card card-pad">
              <h3 style={{ fontSize: 15, marginBottom: 12 }}>Skills you'll learn</h3>
              <div className="skills-list">
                {course.competences_enseignees.map((s) => <span key={s} className="badge badge-semantic">{s}</span>)}
              </div>
            </div>
          )}

          <div className="card card-pad">
            <h3 style={{ fontSize: 15, marginBottom: 12 }}>Prerequisites</h3>
            {course.prerequis_requis.length === 0 ? (
              <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Aucun prérequis — ce cours est accessible directement.</p>
            ) : (
              <div className="skills-list" style={{ marginBottom: 14 }}>
                {course.prerequis_requis.map((s) => <span key={s} className="badge badge-graph">{s}</span>)}
              </div>
            )}
            <button className="btn btn-secondary btn-sm" onClick={() => setShowGraph((v) => !v)}>
              {showGraph ? "Hide prerequisite graph" : "View prerequisite graph"}
            </button>
            {showGraph && (
              <div style={{ marginTop: 16 }}>
                <PrerequisiteGraph rootTitle={course.titre} chain={course.chaine_prerequis} />
              </div>
            )}
          </div>

          {course.cours_relies.length > 0 && (
            <div className="card card-pad">
              <h3 style={{ fontSize: 15, marginBottom: 12 }}>Related Courses</h3>
              <div className="grid-cols-2">
                {course.cours_relies.map((rc) => (
                  <Link key={rc.doc_id} to={`/courses/${rc.doc_id}`} className="course-card" style={{ padding: 14 }}>
                    <p style={{ fontSize: 13.5, fontWeight: 700 }}>{rc.titre}</p>
                    <p className="course-card-meta">{domainLabel(rc.domaine)} · {niveauLabel(rc.niveau)}</p>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="card card-pad">
            <button className="btn btn-primary btn-block" style={{ marginBottom: 14 }}>Start Learning</button>
            {course.formateur && (
              <div className="course-instructor">
                <div className="course-instructor-avatar">{course.formateur.split(" ").map((w) => w[0]).join("")}</div>
                <div>
                  <p style={{ fontSize: 12, color: "var(--text-muted)" }}>Instructor</p>
                  <p style={{ fontSize: 13.5, fontWeight: 600 }}>{course.formateur}</p>
                </div>
              </div>
            )}
            {course.parcours.length > 0 && (
              <div style={{ marginTop: 14 }}>
                <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6 }}>Part of learning path</p>
                {course.parcours.map((p) => <span key={p} className="badge" style={{ marginRight: 6 }}>{p}</span>)}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
