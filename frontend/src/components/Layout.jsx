import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Menu, BookOpen } from "lucide-react";
import Sidebar from "./Sidebar.jsx";

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="app-shell">
      <Sidebar open={mobileOpen} onClose={() => setMobileOpen(false)} />
      <div>
        <header className="topbar">
          <button className="topbar-menu-btn" onClick={() => setMobileOpen(true)} aria-label="Ouvrir le menu">
            <Menu size={18} />
          </button>
          <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 700, fontSize: 14 }}>
            <BookOpen size={16} /> EduSearch
          </div>
          <span style={{ width: 36 }} />
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
