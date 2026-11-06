import { useState } from "react";
import { PROFILE_SKILLS } from "../services/mockData.js";
import { useUser } from "../context/UserContext.jsx";
import { useToast } from "../context/ToastContext.jsx";

export default function Profile() {
  const { user, updateUser } = useUser();
  const { notify } = useToast();
  const [name, setName] = useState(user.name);
  const dirty = name.trim() !== "" && name.trim() !== user.name;

  function handleSave() {
    const trimmed = name.trim();
    if (!trimmed) {
      notify("Le nom ne peut pas être vide.");
      return;
    }
    updateUser({ name: trimmed });
    notify("Nom mis à jour avec succès.", "success");
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>My Profile</h1>
        <p>Vos informations et votre niveau de compétences.</p>
      </div>

      <div className="profile-header">
        <div className="profile-avatar">{user.name.slice(0, 2).toUpperCase()}</div>
        <div>
          <h2 style={{ fontSize: 20 }}>{user.name}</h2>
          <p style={{ fontSize: 13, color: "var(--text-muted)" }}>{user.email}</p>
        </div>
      </div>

      <div className="grid-cols-2">
        <div className="card card-pad">
          <h3 style={{ fontSize: 15, marginBottom: 14 }}>Profile</h3>
          <div className="field" style={{ marginBottom: 12 }}>
            <label>Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSave()}
            />
          </div>
          <div className="field" style={{ marginBottom: 12 }}>
            <label>Email</label>
            <input type="text" value={user.email} readOnly />
          </div>
          <div className="field" style={{ marginBottom: 16 }}>
            <label>Learning Level</label>
            <input type="text" value={user.level} readOnly />
          </div>
          <button className="btn btn-primary" disabled={!dirty} onClick={handleSave}>
            Save changes
          </button>
        </div>

        <div className="card card-pad">
          <h3 style={{ fontSize: 15, marginBottom: 16 }}>My Skills</h3>
          {PROFILE_SKILLS.map((s) => (
            <div className="skill-bar" key={s.label}>
              <div className="skill-bar-top"><span>{s.label}</span><span>{s.value}%</span></div>
              <div className="progress-track"><div className="progress-fill" style={{ width: `${s.value}%` }} /></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
