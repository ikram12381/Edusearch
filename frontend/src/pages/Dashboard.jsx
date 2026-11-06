import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { BookOpen, CheckCircle2, Clock, Search as SearchIcon } from "lucide-react";
import StatCard from "../components/StatCard.jsx";
import ProgressBar from "../components/ProgressBar.jsx";
import CourseCard, { domainLabel, niveauLabel } from "../components/CourseCard.jsx";
import { DASHBOARD_STATS, CONTINUE_LEARNING } from "../services/mockData.js";
import { listCourses } from "../services/api.js";
import { useToast } from "../context/ToastContext.jsx";
import { useUser } from "../context/UserContext.jsx";

export default function Dashboard() {
  const [recommended, setRecommended] = useState([]);
  const { notify } = useToast();
  const { user } = useUser();

  useEffect(() => {
    listCourses({})
      .then((courses) => {
        const top = [...courses].sort((a, b) => b.note - a.note).slice(0, 4);
        setRecommended(top);
      })
      .catch(() => notify("Impossible de charger les cours recommandés (backend indisponible)."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Welcome back, {user.name} 👋</h1>
        <p>Continue your learning journey.</p>
      </div>

      <div className="grid-cols-4" style={{ marginBottom: 28 }}>
        <StatCard icon={BookOpen} value={DASHBOARD_STATS.enrolledCourses} label="Enrolled Courses" tone="primary" />
        <StatCard icon={CheckCircle2} value={DASHBOARD_STATS.completedCourses} label="Completed Courses" tone="success" />
        <StatCard icon={Clock} value={`${DASHBOARD_STATS.learningHours}h`} label="Learning Hours" tone="semantic" />
        <StatCard icon={SearchIcon} value={DASHBOARD_STATS.searchQueries} label="Search Queries" tone="graph" />
      </div>

      <div className="page-header-row" style={{ marginBottom: 14 }}>
        <h2 style={{ fontSize: 18 }}>Continue Learning</h2>
        <Link to="/learning" className="btn btn-ghost btn-sm">View all</Link>
      </div>
      <div className="grid-cols-3" style={{ marginBottom: 32 }}>
        {CONTINUE_LEARNING.map((c) => (
          <div key={c.doc_id} className="course-card">
            <Link to={`/courses/${c.doc_id}`} className="course-card-title">{c.titre}</Link>
            <p className="course-card-meta">{domainLabel(c.domaine)} · {niveauLabel(c.niveau)}</p>
            <ProgressBar value={c.progress} />
            <p style={{ fontSize: 12, color: "var(--text-muted)" }}>{c.progress}% completed</p>
            <Link to={`/courses/${c.doc_id}`} className="btn btn-primary btn-sm btn-block">Continue Learning</Link>
          </div>
        ))}
      </div>

      <div className="page-header-row" style={{ marginBottom: 14 }}>
        <h2 style={{ fontSize: 18 }}>Recommended for you</h2>
        <Link to="/courses" className="btn btn-ghost btn-sm">Explore all</Link>
      </div>
      <div className="grid-auto-fill">
        {recommended.map((c) => <CourseCard key={c.doc_id} course={c} />)}
      </div>
    </div>
  );
}
