import { Link } from "react-router-dom";
import { Star, Bookmark, Clock } from "lucide-react";
import { useFavorites } from "../context/FavoritesContext.jsx";

const NIVEAU_LABEL = { Debutant: "Beginner", Intermediaire: "Intermediate", Avance: "Advanced" };
const DOMAIN_LABEL = {
  Informatique: "Computer Science", DataScience: "Data Science", BigData: "Big Data",
  IntelligenceArtificielle: "Artificial Intelligence", MachineLearning: "Machine Learning",
  DeepLearning: "Deep Learning", NLP: "NLP", DeveloppementWeb: "Web Development",
  Cloud: "Cloud", DevOps: "DevOps", BasesDeDonnees: "Databases", CyberSecurite: "Cybersecurity",
  Langues: "Languages", Mathematiques: "Mathematics",
};

export function domainLabel(id) {
  return DOMAIN_LABEL[id] || id;
}
export function niveauLabel(id) {
  return NIVEAU_LABEL[id] || id;
}

export default function CourseCard({ course, scoreLabel, scoreValue }) {
  const { isFavorite, toggleFavorite } = useFavorites();
  const fav = isFavorite(course.doc_id);

  return (
    <div className="course-card fade-in-up">
      <div className="course-card-top">
        <div>
          <Link to={`/courses/${course.doc_id}`} className="course-card-title">{course.titre}</Link>
          <p className="course-card-meta">
            {domainLabel(course.domaine)} · {niveauLabel(course.niveau)}
            {course.duree_heures != null ? ` · ${course.duree_heures}h` : ""}
          </p>
        </div>
        <button
          className={`bookmark-btn ${fav ? "active" : ""}`}
          onClick={() => toggleFavorite(course.doc_id)}
          aria-label={fav ? "Retirer des favoris" : "Ajouter aux favoris"}
        >
          <Bookmark />
        </button>
      </div>

      {course.description && <p className="course-card-desc">{course.description}</p>}

      <div className="course-card-bottom">
        <div className="course-card-rating">
          <Star />
          {course.note != null ? course.note.toFixed(1) : "—"}
          {course.gratuit != null && (
            <span className={`badge ${course.gratuit ? "badge-success" : ""}`} style={{ marginLeft: 6 }}>
              {course.gratuit ? "Free" : "Paid"}
            </span>
          )}
        </div>
        {scoreValue != null ? (
          <span className="badge badge-primary">{scoreLabel || "score"} {scoreValue}</span>
        ) : (
          course.duree_heures != null && (
            <span className="badge"><Clock size={11} /> {course.duree_heures}h</span>
          )
        )}
      </div>
    </div>
  );
}
