import { useEffect, useState } from "react";
import { Bookmark } from "lucide-react";
import CourseCard from "../components/CourseCard.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { useFavorites } from "../context/FavoritesContext.jsx";
import { getCourse } from "../services/api.js";

export default function Favorites() {
  const { favorites } = useFavorites();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (favorites.length === 0) {
      setCourses([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.allSettled(favorites.map((id) => getCourse(id)))
      .then((results) => setCourses(results.filter((r) => r.status === "fulfilled").map((r) => r.value)))
      .finally(() => setLoading(false));
  }, [favorites]);

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Favorites</h1>
        <p>Les cours que vous avez sauvegardés.</p>
      </div>

      {loading && favorites.length > 0 && (
        <div className="grid-auto-fill">
          {favorites.map((id) => <div key={id} className="skeleton" style={{ height: 170, borderRadius: "var(--radius)" }} />)}
        </div>
      )}

      {!loading && courses.length === 0 && (
        <EmptyState icon={Bookmark} title="Aucun favori pour l'instant" message="Cliquez sur l'icône bookmark d'un cours pour l'ajouter ici." />
      )}

      {!loading && courses.length > 0 && (
        <div className="grid-auto-fill">
          {courses.map((c) => <CourseCard key={c.doc_id} course={c} />)}
        </div>
      )}
    </div>
  );
}
