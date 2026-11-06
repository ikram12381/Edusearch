export default function EmptyState({ icon: Icon, title, message }) {
  return (
    <div className="empty-state fade-in">
      {Icon && <div className="empty-state-icon"><Icon /></div>}
      <h3>{title}</h3>
      {message && <p>{message}</p>}
    </div>
  );
}
