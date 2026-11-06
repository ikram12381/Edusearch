import { useEffect, useState } from "react";
import { Compass } from "lucide-react";
import Filters from "../components/Filters.jsx";
import CourseCard from "../components/CourseCard.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { listCourses, getDomainGraph } from "../services/api.js";
import { useToast } from "../context/ToastContext.jsx";

export default function Explore() {
  const [courses, setCourses] = useState([]);
  const [domains, setDomains] = useState([]);
  const [filters, setFilters] = useState({});
  const [loading, setLoading] = useState(true);
  const { notify } = useToast();

  useEffect(() => {
    getDomainGraph().then((g) => setDomains(g.nodes.map((n) => ({ id: n.id, label: n.label })))).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const apiFilters = {
      domaine: filters.domaine,
      niveau: filters.niveau,
      duree_max: filters.duree_max,
      note_min: filters.note_min,
      gratuit: filters.gratuit,
    };
    listCourses(apiFilters)
      .then(setCourses)
      .catch(() => notify("Impossible de charger le catalogue de cours."))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Explore Courses</h1>
        <p>Parcourez le catalogue complet — {courses.length} cours disponibles.</p>
      </div>

      <div className="search-layout">
        <Filters domains={domains} value={filters} onChange={setFilters} />
        <div>
          {loading && (
            <div className="grid-auto-fill">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="skeleton" style={{ height: 170, borderRadius: "var(--radius)" }} />
              ))}
            </div>
          )}
          {!loading && courses.length === 0 && (
            <EmptyState icon={Compass} title="Aucun cours ne correspond" message="Essayez d'élargir ou de réinitialiser vos filtres." />
          )}
          {!loading && courses.length > 0 && (
            <div className="grid-auto-fill">
              {courses.map((c) => <CourseCard key={c.doc_id} course={c} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
