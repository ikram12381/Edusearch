import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Search as SearchIcon, Compass, GraduationCap, Bookmark,
  Share2, BarChart3, User, Settings, Moon, Sun, LogOut, BookOpen, GitCompare,
} from "lucide-react";
import { useTheme } from "../context/ThemeContext.jsx";
import { useUser } from "../context/UserContext.jsx";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/search", label: "Search", icon: SearchIcon },
  { to: "/compare", label: "Compare Search", icon: GitCompare },
  { to: "/courses", label: "Explore Courses", icon: Compass },
  { to: "/learning", label: "My Learning", icon: GraduationCap },
  { to: "/favorites", label: "Favorites", icon: Bookmark },
  { to: "/knowledge-graph", label: "Knowledge Graph", icon: Share2 },
  { to: "/evaluation", label: "Search Evaluation", icon: BarChart3 },
  { to: "/profile", label: "Profile", icon: User },
];

export default function Sidebar({ open, onClose }) {
  const { theme, toggleTheme } = useTheme();
  const { user } = useUser();

  return (
    <>
      <div className={`sidebar-backdrop ${open ? "open" : ""}`} onClick={onClose} />
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="sidebar-brand">
          <div className="sidebar-brand-mark"><BookOpen size={18} /></div>
          <div className="sidebar-brand-text">
            <h1>EduSearch</h1>
            <span>Learn smarter. Search beyond keywords.</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <span className="sidebar-section-label">Navigation</span>
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onClose}
              className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
            >
              <Icon /> {label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button className="sidebar-link" onClick={toggleTheme} style={{ width: "100%", border: "none", background: "none", cursor: "pointer" }}>
            {theme === "dark" ? <Sun /> : <Moon />} {theme === "dark" ? "Light mode" : "Dark mode"}
          </button>
          <NavLink to="/profile" className="sidebar-link"><Settings /> Settings</NavLink>
          <NavLink to="/login" className="sidebar-link"><LogOut /> Logout</NavLink>

          <div className="sidebar-user">
            <div className="sidebar-user-avatar">{user.name.slice(0, 2).toUpperCase()}</div>
            <div className="sidebar-user-info">
              <p>{user.name}</p>
              <span>{user.level}</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
