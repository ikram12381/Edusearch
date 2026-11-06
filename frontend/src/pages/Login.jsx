import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { BookOpen } from "lucide-react";
import { useUser } from "../context/UserContext.jsx";

export default function Login() {
  const [tab, setTab] = useState("Login");
  const navigate = useNavigate();
  const { user, updateUser } = useUser();
  const [name, setName] = useState(user.name);
  const [email, setEmail] = useState(user.email);

  function handleSubmit(e) {
    e.preventDefault();
    // Démo académique : pas d'authentification réelle, on simule simplement
    // la connexion de l'utilisateur et on redirige vers le Dashboard.
    if (tab === "Sign Up") {
      updateUser({ name: name.trim() || user.name, email: email.trim() || user.email });
    }
    navigate("/dashboard");
  }

  return (
    <div className="auth-shell">
      <div className="auth-card fade-in-up">
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 22 }}>
          <div className="sidebar-brand-mark"><BookOpen size={18} /></div>
          <h1 style={{ fontSize: 16, fontWeight: 700 }}>EduSearch</h1>
        </div>

        <div className="auth-tabs">
          <div className={`auth-tab ${tab === "Login" ? "active" : ""}`} onClick={() => setTab("Login")}>Login</div>
          <div className={`auth-tab ${tab === "Sign Up" ? "active" : ""}`} onClick={() => setTab("Sign Up")}>Sign Up</div>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {tab === "Sign Up" && (
            <div className="field">
              <label>Name</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
          )}
          <div className="field">
            <label>Email</label>
            <input type="text" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="text" defaultValue="••••••••" />
          </div>
          <button type="submit" className="btn btn-primary btn-block" style={{ marginTop: 6 }}>
            {tab === "Login" ? "Log in" : "Create account"}
          </button>
        </form>
        <p style={{ fontSize: 11.5, color: "var(--text-faint)", marginTop: 16, textAlign: "center" }}>
          Démo académique — utilisateur simulé, sans authentification réelle.
        </p>
      </div>
    </div>
  );
}
