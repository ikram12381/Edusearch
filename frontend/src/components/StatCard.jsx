export default function StatCard({ icon: Icon, value, label, tone = "primary" }) {
  return (
    <div className="stat-card">
      <div className="stat-card-top">
        <div className="stat-card-icon" style={{ background: `var(--${tone}-soft)`, color: `var(--${tone})` }}>
          <Icon />
        </div>
      </div>
      <div className="stat-card-value">{value}</div>
      <div className="stat-card-label">{label}</div>
    </div>
  );
}
